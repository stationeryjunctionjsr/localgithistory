import os
import sys
import subprocess
import csv

user_counts = [1, 50, 100, 250, 400, 500, 600]
spawn_rate = 50

results = []

for users in user_counts:
    print(f"Running test for {users} users...")
    csv_prefix = f"load_{users}"
    cmd = [
        sys.executable,
        "-m", "locust",
        "-f", "locustfile.py",
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate if users > spawn_rate else users),
        "--run-time", "15s",
        "--host", "http://127.0.0.1:8000",
        "--csv", csv_prefix,
        "--exit-code-on-error", "0"
    ]
    
    # We use creationflags=subprocess.CREATE_NO_WINDOW in windows to avoid popup
    subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    
    # Read the generated CSV
    stats_file = f"{csv_prefix}_stats.csv"
    with open(stats_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] == "Aggregated":
                results.append({
                    "Users": users,
                    "Median (p50)": row.get("Median Response Time", "N/A"),
                    "Average": row.get("Average Response Time", "N/A"),
                    "p90": row.get("90%", "N/A"),
                    "p95": row.get("95%", "N/A"),
                    "p99": row.get("99%", "N/A"),
                    "RPS": row.get("Requests/s", "N/A"),
                    "Failures/s": row.get("Failures/s", "N/A")
                })
                break

# Print final table
print("\n" + "="*90)
print(f"{'Users':<10} | {'Median(p50)':<12} | {'Average':<10} | {'p90':<10} | {'p95':<10} | {'p99':<10} | {'RPS':<10} | {'Fail/s':<10}")
print("-" * 90)
for r in results:
    print(f"{r['Users']:<10} | {r['Median (p50)']:<12} | {r['Average']:<10} | {r['p90']:<10} | {r['p95']:<10} | {r['p99']:<10} | {r['RPS']:<10} | {r['Failures/s']:<10}")
print("="*90)
