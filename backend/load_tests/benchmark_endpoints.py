"""
Endpoint Latency Benchmarker
=============================
Runs sequential HTTP requests against every critical endpoint and reports:
  - Mean, P50, P90, P99 response times
  - Min / Max
  - Error count
  - Pass/Fail against SLA thresholds

Usage (from backend/ directory):
  python load_tests/benchmark_endpoints.py

Optional env vars:
  TEST_CUSTOMER_TOKEN  — enables auth endpoint benchmarking
  TEST_ADMIN_TOKEN     — enables admin endpoint benchmarking
  LOAD_TEST_BASE_URL   — override base URL (default: http://localhost:8000)
  BENCHMARK_REPS       — number of repetitions per endpoint (default: 20)
"""

import os
import sys
import statistics
import time
from datetime import datetime
from typing import Optional

import httpx

# ── Path fix ──────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from load_tests.config import (
    ADMIN_ENDPOINTS,
    AUTH_ENDPOINTS,
    BASE_URL,
    PUBLIC_ENDPOINTS,
    REPORTS_DIR,
    SLA,
    TEST_ADMIN_TOKEN,
    TEST_CUSTOMER_TOKEN,
)

REPS = int(os.getenv("BENCHMARK_REPS", "20"))
TIMEOUT = 15.0  # seconds per request


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


def _color_ms(value_ms: float, warn_ms: float, fail_ms: float) -> str:
    s = f"{value_ms:.0f} ms"
    if value_ms <= warn_ms:
        return _green(s)
    elif value_ms <= fail_ms:
        return _yellow(s)
    return _red(s)


# ── Core benchmark function ───────────────────────────────────────────────────


def benchmark_endpoint(
    client: httpx.Client,
    method: str,
    path: str,
    label: str,
    headers: Optional[dict] = None,
    reps: int = REPS,
) -> dict:
    """
    Make `reps` requests to `method path` and collect timing statistics.
    Returns a result dict suitable for reporting.
    """
    url = BASE_URL + path
    timings_ms = []
    errors = []

    for i in range(reps):
        try:
            t0 = time.perf_counter()
            resp = client.request(method, url, headers=headers or {}, timeout=TIMEOUT)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            timings_ms.append(elapsed_ms)

            # Treat server errors as failures but still record timing
            if resp.status_code >= 500:
                errors.append(f"HTTP {resp.status_code}")
        except httpx.TimeoutException:
            errors.append("TIMEOUT")
            timings_ms.append(TIMEOUT * 1000)
        except Exception as e:
            errors.append(str(e))
            timings_ms.append(TIMEOUT * 1000)

    if not timings_ms:
        return {"label": label, "path": path, "method": method, "error": "All requests failed"}

    sorted_t = sorted(timings_ms)
    n = len(sorted_t)

    def percentile(pct):
        idx = max(0, int(n * pct / 100) - 1)
        return sorted_t[idx]

    return {
        "label": label,
        "method": method,
        "path": path,
        "reps": reps,
        "mean_ms": statistics.mean(timings_ms),
        "median_ms": statistics.median(timings_ms),
        "p50_ms": percentile(50),
        "p90_ms": percentile(90),
        "p99_ms": percentile(99),
        "min_ms": min(timings_ms),
        "max_ms": max(timings_ms),
        "stdev_ms": statistics.stdev(timings_ms) if n > 1 else 0,
        "errors": errors,
        "error_count": len(errors),
        "error_rate_pct": (len(errors) / reps) * 100,
    }


# ── Reporting ─────────────────────────────────────────────────────────────────


def print_results_table(results: list[dict]):
    col_w = [40, 8, 8, 8, 8, 8, 8, 6]
    headers = ["Endpoint", "Mean", "P50", "P90", "P99", "Min", "Max", "Errs"]
    sep = "-" * (sum(col_w) + len(col_w) * 3)

    print()
    print(_bold(_cyan(sep)))
    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_w))
    print(_bold(f"  {header_row}"))
    print(_bold(_cyan(sep)))

    all_passed = True
    for r in results:
        if "error" in r:
            label_str = r["label"][: col_w[0]].ljust(col_w[0])
            print(f"  {label_str}  {_red('ALL FAILED')}")
            all_passed = False
            continue

        # SLA checks
        p50_ok = r["p50_ms"] <= SLA["p50_ms"]
        p90_ok = r["p90_ms"] <= SLA["p90_ms"]
        p99_ok = r["p99_ms"] <= SLA["p99_ms"]
        if not (p50_ok and p90_ok and p99_ok):
            all_passed = False

        label_str = r["label"][: col_w[0]].ljust(col_w[0])
        mean_s = _color_ms(r["mean_ms"], SLA["p50_ms"], SLA["p90_ms"])
        p50_s = _color_ms(r["p50_ms"], SLA["p50_ms"], SLA["p90_ms"])
        p90_s = _color_ms(r["p90_ms"], SLA["p90_ms"], SLA["p99_ms"])
        p99_s = _color_ms(r["p99_ms"], SLA["p99_ms"], SLA["p99_ms"] * 2)
        min_s = f"{r['min_ms']:.0f} ms"
        max_s = f"{r['max_ms']:.0f} ms"
        err_s = _red(str(r["error_count"])) if r["error_count"] else _green("0")

        row = f"  {label_str}  {mean_s:<8}  {p50_s:<8}  {p90_s:<8}  {p99_s:<8}  {min_s:<8}  {max_s:<8}  {err_s}"
        print(row)

    print(_bold(_cyan(sep)))
    return all_passed


def save_html_report(results: list[dict], title: str, filepath: str):
    """Save results as a self-contained HTML table."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows_html = ""
    for r in results:
        if "error" in r:
            rows_html += f"<tr><td>{r['label']}</td><td colspan='7' style='color:red'>ALL FAILED</td></tr>\n"
            continue

        def cell(val_ms, warn, fail):
            color = "green" if val_ms <= warn else ("orange" if val_ms <= fail else "red")
            return f"<td style='color:{color}'>{val_ms:.0f} ms</td>"

        err_color = "red" if r["error_count"] else "green"
        rows_html += (
            f"<tr>"
            f"<td>{r['label']}</td>"
            f"<td>{r['method']}</td>"
            f"{cell(r['mean_ms'], SLA['p50_ms'], SLA['p90_ms'])}"
            f"{cell(r['p50_ms'], SLA['p50_ms'], SLA['p90_ms'])}"
            f"{cell(r['p90_ms'], SLA['p90_ms'], SLA['p99_ms'])}"
            f"{cell(r['p99_ms'], SLA['p99_ms'], SLA['p99_ms'] * 2)}"
            f"<td>{r['min_ms']:.0f} ms</td>"
            f"<td>{r['max_ms']:.0f} ms</td>"
            f"<td style='color:{err_color}'>{r['error_count']}</td>"
            f"</tr>\n"
        )

    sla_note = f"SLA Thresholds — P50: {SLA['p50_ms']} ms | P90: {SLA['p90_ms']} ms | P99: {SLA['p99_ms']} ms"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }}
  h1 {{ color: #38bdf8; font-size: 1.5rem; margin-bottom: 0.25rem; }}
  p.meta {{ color: #94a3b8; font-size: 0.85rem; margin-bottom: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
  th {{ background: #1e293b; color: #7dd3fc; padding: 10px 14px; text-align: left; border-bottom: 2px solid #334155; }}
  td {{ padding: 8px 14px; border-bottom: 1px solid #1e293b; }}
  tr:hover td {{ background: #1e293b44; }}
  .legend {{ margin-top: 1.5rem; font-size: 0.8rem; color: #64748b; }}
  .legend span {{ margin-right: 1.5rem; }}
  .pass {{ color: #4ade80; }} .warn {{ color: #facc15; }} .fail {{ color: #f87171; }}
</style>
</head>
<body>
<h1>📊 {title}</h1>
<p class="meta">Generated: {now} | Repetitions per endpoint: {REPS} | Base URL: {BASE_URL}</p>
<table>
  <thead>
    <tr>
      <th>Endpoint</th><th>Method</th><th>Mean</th><th>P50</th>
      <th>P90</th><th>P99</th><th>Min</th><th>Max</th><th>Errors</th>
    </tr>
  </thead>
  <tbody>
{rows_html}
  </tbody>
</table>
<div class="legend">
  <strong>Legend:</strong>
  <span class="pass">■ Within SLA</span>
  <span class="warn">■ Near threshold</span>
  <span class="fail">■ Exceeds SLA</span>
  &nbsp;|&nbsp; {sla_note}
</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  [HTML] HTML report saved -> {filepath}")


def save_csv_report(results: list[dict], filepath: str):
    """Save results as CSV for further analysis."""
    import csv

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = [
        "label",
        "method",
        "path",
        "reps",
        "mean_ms",
        "p50_ms",
        "p90_ms",
        "p99_ms",
        "min_ms",
        "max_ms",
        "stdev_ms",
        "error_count",
        "error_rate_pct",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            if "error" not in r:
                writer.writerow(r)
    print(f"  [CSV] CSV report saved -> {filepath}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print(_bold(_cyan("\n======================================================")))
    print(_bold(_cyan("  Stationery Junction - Endpoint Latency Benchmarker  ")))
    print(_bold(_cyan("======================================================")))
    print(f"  Base URL : {BASE_URL}")
    print(f"  Reps/endpoint: {REPS}")
    print(f"  Auth tests: {'[PASS] customer token set' if TEST_CUSTOMER_TOKEN else '[SKIP] customer token not set'}")
    print(f"  Admin tests: {'[PASS] admin token set' if TEST_ADMIN_TOKEN else '[SKIP] admin token not set'}")
    print()

    all_results = []

    with httpx.Client(timeout=TIMEOUT) as client:
        # ── 1. Public endpoints ────────────────────────────────────────────────
        print(_bold("[ Public Endpoints ]"))
        for method, path, label in PUBLIC_ENDPOINTS:
            print(f"  Testing {label}...", end="\r")
            r = benchmark_endpoint(client, method, path, label)
            all_results.append(r)
        public_pass = print_results_table([r for r in all_results])

        # ── 2. Authenticated (customer) endpoints ──────────────────────────────
        if TEST_CUSTOMER_TOKEN:
            print(_bold("\n[ Authenticated Customer Endpoints ]"))
            auth_headers = {"Authorization": f"Bearer {TEST_CUSTOMER_TOKEN}"}
            auth_results = []
            for method, path, label in AUTH_ENDPOINTS:
                print(f"  Testing {label}...", end="\r")
                r = benchmark_endpoint(client, method, path, label, headers=auth_headers)
                auth_results.append(r)
                all_results.append(r)
            print_results_table(auth_results)
        else:
            print(_yellow("\n  [SKIP] Skipping customer auth endpoints (set TEST_CUSTOMER_TOKEN)"))

        # ── 3. Admin endpoints ─────────────────────────────────────────────────
        if TEST_ADMIN_TOKEN:
            print(_bold("\n[ Admin Endpoints ]"))
            admin_headers = {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}
            admin_results = []
            for method, path, label in ADMIN_ENDPOINTS:
                print(f"  Testing {label}...", end="\r")
                r = benchmark_endpoint(client, method, path, label, headers=admin_headers)
                admin_results.append(r)
                all_results.append(r)
            print_results_table(admin_results)
        else:
            print(_yellow("  [SKIP] Skipping admin endpoints (set TEST_ADMIN_TOKEN)"))

    # ── Summary ──────────────────────────────────────────────────────────────
    total = len(all_results)
    passed = sum(
        1
        for r in all_results
        if "error" not in r
        and r["p50_ms"] <= SLA["p50_ms"]
        and r["p90_ms"] <= SLA["p90_ms"]
        and r["p99_ms"] <= SLA["p99_ms"]
        and r["error_count"] == 0
    )
    failed = total - passed

    print()
    if failed == 0:
        print(_green(f"  [PASS] All {total} endpoints passed SLA thresholds"))
    else:
        print(_red(f"  [FAIL] {failed}/{total} endpoints FAILED SLA thresholds"))

    # ── Save reports ──────────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(REPORTS_DIR, f"benchmark_{ts}.html")
    csv_path = os.path.join(REPORTS_DIR, f"benchmark_{ts}.csv")
    save_html_report(all_results, "Endpoint Latency Benchmark", html_path)
    save_csv_report(all_results, csv_path)

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
