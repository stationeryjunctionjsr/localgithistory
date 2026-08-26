"""
Automated Load Test Runner
===========================
Runs Locust in headless mode sequentially through all profiles:
  1. baseline  (1 user,   30 s)
  2. load      (50 users,  2 min)
  3. stress    (100 users, 3 min)
  4. spike     (200 users, 1 min)

After all runs, prints a consolidated pass/fail summary comparing
each profile's results against SLA thresholds.

Usage (from backend/ directory):
  python load_tests/run_load_tests.py [--profiles baseline load]

Requirements:
  - Locust installed in the current venv (`pip install locust`)
  - Backend running at BASE_URL (default: http://localhost:8000)

Output:
  - HTML report per profile: load_tests/reports/<profile>_<timestamp>.html
  - CSV stats per profile:   load_tests/reports/<profile>_<timestamp>_stats.csv
  - Consolidated summary printed to stdout

Environment Variables:
  TEST_CUSTOMER_TOKEN  — Bearer token for customer auth tasks
  TEST_ADMIN_TOKEN     — Bearer token for admin tasks
  LOAD_TEST_BASE_URL   — Override target URL
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Path fix ──────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from load_tests.config import BASE_URL, PROFILES, REPORTS_DIR, SLA


# ── Colour helpers ────────────────────────────────────────────────────────────
def _green(s):
    return f"\033[92m{s}\033[0m"


def _yellow(s):
    return f"\033[93m{s}\033[0m"


def _red(s):
    return f"\033[91m{s}\033[0m"


def _bold(s):
    return f"\033[1m{s}\033[0m"


def _cyan(s):
    return f"\033[96m{s}\033[0m"


LOCUSTFILE = os.path.join(os.path.dirname(__file__), "locustfile.py")


def run_profile(profile_name: str, profile: dict, ts: str) -> dict:
    """Run a single Locust profile headlessly and return parsed stats."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    html_report = os.path.join(REPORTS_DIR, f"{profile_name}_{ts}.html")
    csv_prefix = os.path.join(REPORTS_DIR, f"{profile_name}_{ts}")

    users = profile["users"]
    spawn_rate = profile["spawn_rate"]
    run_time = profile["run_time"]

    print()
    print(_bold(_cyan(f"[RUN] Running profile: {profile_name.upper()}")))
    print(f"  {profile['description']}")
    print(f"  Users: {users} | Spawn: {spawn_rate}/s | Duration: {run_time}")
    print()

    cmd = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        LOCUSTFILE,
        "--host",
        BASE_URL,
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "-t",
        run_time,
        "--html",
        html_report,
        "--csv",
        csv_prefix,
        "--only-summary",
        "--stop-timeout",
        "10",
    ]

    env = os.environ.copy()
    # Pass tokens through if set
    for key in ("TEST_CUSTOMER_TOKEN", "TEST_ADMIN_TOKEN", "LOAD_TEST_BASE_URL"):
        if os.getenv(key):
            env[key] = os.getenv(key)

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(__file__)),  # backend/
            env=env,
            capture_output=False,
            timeout=600,  # max 10-min safety timeout
        )
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        print(_red("  [WARN] Locust timed out after 10 minutes — killing."))
        returncode = -1
    except FileNotFoundError:
        print(_red("  [FAIL] Locust not found in PATH. Run: pip install locust"))
        return {"profile": profile_name, "error": "locust not found"}

    elapsed = time.time() - start
    print(f"\n  Profile '{profile_name}' finished in {elapsed:.0f}s (exit code: {returncode})")
    print(f"  [HTML] HTML report -> {html_report}")

    # ── Parse CSV stats ───────────────────────────────────────────────────────
    stats_csv = csv_prefix + "_stats.csv"
    stats = parse_locust_csv(stats_csv)
    stats["profile"] = profile_name
    stats["html_report"] = html_report
    stats["csv_prefix"] = csv_prefix
    stats["returncode"] = returncode

    return stats


def parse_locust_csv(csv_path: str) -> dict:
    """Parse Locust stats CSV and return aggregated metrics."""
    if not os.path.exists(csv_path):
        return {"parse_error": f"CSV not found: {csv_path}"}

    rows = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        return {"parse_error": str(e)}

    # Find the "Aggregated" row
    agg = None
    for row in rows:
        name = row.get("Name", "").strip()
        if name.lower() in ("aggregated", "total", "aggregate"):
            agg = row
            break

    if not agg and rows:
        agg = rows[-1]  # last row is usually aggregated

    if not agg:
        return {"parse_error": "No aggregated row found in CSV"}

    def _float(key, default=0.0):
        try:
            return float(agg.get(key, default) or default)
        except (ValueError, TypeError):
            return default

    total_req = _float("Request Count")
    fail_req = _float("Failure Count")
    error_rate = (fail_req / total_req * 100) if total_req > 0 else 0.0

    return {
        "total_requests": int(total_req),
        "failures": int(fail_req),
        "error_rate_pct": error_rate,
        "rps": _float("Requests/s"),
        "p50_ms": _float("50%"),
        "p90_ms": _float("90%"),
        "p99_ms": _float("99%"),
        "mean_ms": _float("Average (ms)"),
        "max_ms": _float("Max (ms)"),
        "min_ms": _float("Min (ms)"),
    }


def evaluate_sla(stats: dict, profile_name: str) -> bool:
    """Return True if the profile's stats pass SLA."""
    if "error" in stats or "parse_error" in stats:
        return False

    # Use stricter thresholds for non-stress profiles
    is_stress = profile_name in ("stress", "spike")
    max_err = SLA["stress_error_rate_pct"] if is_stress else SLA["error_rate_pct"]

    checks = [
        ("P50 response time", stats.get("p50_ms", 9999), SLA["p50_ms"]),
        ("P90 response time", stats.get("p90_ms", 9999), SLA["p90_ms"]),
        ("P99 response time", stats.get("p99_ms", 9999), SLA["p99_ms"]),
        ("Error rate %", stats.get("error_rate_pct", 100), max_err),
    ]
    all_pass = True
    for name, actual, threshold in checks:
        if actual > threshold:
            print(_red(f"    [FAIL] {name}: {actual:.1f} > threshold {threshold}"))
            all_pass = False
        else:
            print(_green(f"    [PASS] {name}: {actual:.1f} <= {threshold}"))
    return all_pass


def print_summary(all_stats: list[dict]):
    """Print a consolidated table of all profile results."""
    print()
    print(_bold(_cyan("===========================================================")))
    print(_bold(_cyan("  CONSOLIDATED LOAD TEST SUMMARY")))
    print(_bold(_cyan("===========================================================")))
    print(
        f"  {'Profile':<12} {'Requests':>10} {'Errors':>8} {'Err%':>6} "
        f"{'RPS':>7} {'P50':>8} {'P90':>8} {'P99':>8} {'SLA':>6}"
    )
    print("  " + "-" * 77)

    all_pass = True
    for s in all_stats:
        pname = s.get("profile", "?")
        if "error" in s or "parse_error" in s:
            err_msg = s.get("error") or s.get("parse_error", "unknown error")
            print(f"  {pname:<12} {_red(f'FAILED: {err_msg}')}")
            all_pass = False
            continue

        is_stress = pname in ("stress", "spike")
        max_err = SLA["stress_error_rate_pct"] if is_stress else SLA["error_rate_pct"]

        ok = (
            s.get("p50_ms", 9999) <= SLA["p50_ms"]
            and s.get("p90_ms", 9999) <= SLA["p90_ms"]
            and s.get("p99_ms", 9999) <= SLA["p99_ms"]
            and s.get("error_rate_pct", 100) <= max_err
        )
        if not ok:
            all_pass = False

        status = _green("PASS") if ok else _red("FAIL")
        err_pct = s.get("error_rate_pct", 0)
        err_col = _red(f"{err_pct:.1f}%") if err_pct > max_err else f"{err_pct:.1f}%"

        p50 = s.get("p50_ms", 0)
        p90 = s.get("p90_ms", 0)
        p99 = s.get("p99_ms", 0)

        p50_s = _red(f"{p50:.0f}ms") if p50 > SLA["p50_ms"] else f"{p50:.0f}ms"
        p90_s = _red(f"{p90:.0f}ms") if p90 > SLA["p90_ms"] else f"{p90:.0f}ms"
        p99_s = _red(f"{p99:.0f}ms") if p99 > SLA["p99_ms"] else f"{p99:.0f}ms"

        print(
            f"  {pname:<12} "
            f"{s.get('total_requests', 0):>10,} "
            f"{s.get('failures', 0):>8,} "
            f"{err_col:>6} "
            f"{s.get('rps', 0):>7.1f} "
            f"{p50_s:>8} "
            f"{p90_s:>8} "
            f"{p99_s:>8} "
            f"{status:>6}"
        )

    print("  " + "-" * 77)
    if all_pass:
        print(_green("  [PASS] All profiles passed SLA thresholds!"))
    else:
        print(_red("  [FAIL] One or more profiles FAILED SLA thresholds."))
    print()

    # Print report file locations
    print(_bold("  [DIR] Reports saved to:"), REPORTS_DIR)
    for s in all_stats:
        if "html_report" in s:
            pname = s.get("profile", "?")
            print(f"     [{pname}] {s['html_report']}")
    print()


def save_json_summary(all_stats: list[dict], ts: str):
    """Save a machine-readable JSON summary of all runs."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"summary_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=2)
    print(f"  [JSON] JSON summary -> {path}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Automated Locust load test runner — runs all profiles in sequence.")
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=list(PROFILES.keys()),
        default=list(PROFILES.keys()),
        help="Which profiles to run (default: all)",
    )
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(_bold(_cyan("\n+------------------------------------------------------+")))
    print(_bold(_cyan("|  Stationery Junction - Automated Load Test Runner    |")))
    print(_bold(_cyan("+------------------------------------------------------+")))
    print(f"  Target URL : {BASE_URL}")
    print(f"  Profiles   : {', '.join(args.profiles)}")
    print(f"  Timestamp  : {ts}")
    print()

    # Quick connectivity check
    import httpx

    try:
        resp = httpx.get(f"{BASE_URL}/api/health", timeout=5)
        print(_green(f"  [PASS] API reachable — {BASE_URL}/api/health -> HTTP {resp.status_code}"))
        
        print(_cyan("  [WAIT] Warming up critical endpoints to prevent cold-start latency..."))
        for ep in [
            "/api/categories/public",
            "/api/products/public",
            "/api/promo-strips",
            "/api/recommendations"
        ]:
            try:
                httpx.get(f"{BASE_URL}{ep}", timeout=10)
            except Exception:
                pass
        print(_green("  [PASS] Caches and DB connections warmed up!"))

    except Exception as e:
        print(_red(f"  [FAIL] Cannot reach {BASE_URL}/api/health: {e}"))
        print(_red("    Start the backend first, then re-run this script."))
        sys.exit(1)

    all_stats = []

    for pname in args.profiles:
        profile = PROFILES[pname]
        stats = run_profile(pname, profile, ts)
        all_stats.append(stats)

        # SLA evaluation after each run
        print(f"\n  SLA check for '{pname}':")
        evaluate_sla(stats, pname)

        # Small cooldown between profiles
        if args.profiles.index(pname) < len(args.profiles) - 1:
            cooldown = 15
            print(f"\n  [WAIT] Cooling down {cooldown}s before next profile...")
            time.sleep(cooldown)

    print_summary(all_stats)
    save_json_summary(all_stats, ts)

    # Overall exit code
    all_pass = all(
        "error" not in s
        and "parse_error" not in s
        and s.get("p50_ms", 9999) <= SLA["p50_ms"]
        and s.get("p90_ms", 9999) <= SLA["p90_ms"]
        and s.get("p99_ms", 9999) <= SLA["p99_ms"]
        for s in all_stats
    )
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
