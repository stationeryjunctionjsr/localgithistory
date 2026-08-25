import subprocess
import re
import os

vus_list = [1, 50, 100, 250, 400, 500, 600]
results = []

for vus in vus_list:
    duration = "5m" if vus == 600 else "2m"
    print(f"Running {duration} test for {vus} users...")
    cmd = [
        r"c:\Ecommerce app\k6-v0.50.0-windows-amd64\k6.exe",
        "run",
        "-e", f"VUS={vus}",
        "-e", f"DURATION={duration}",
        r"c:\Ecommerce app\incremental_test.js"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    
    avg_dur = min_dur = med_dur = max_dur = p90_dur = p95_dur = p99_dur = "N/A"
    fail_rate = "N/A"
    reqs_per_sec = "N/A"
    
    for line in output.split('\n'):
        if "http_req_duration" in line and "expected_response" not in line:
            m_avg = re.search(r"avg=([\d\.]+m?s?)", line)
            m_min = re.search(r"min=([\d\.]+m?s?)", line)
            m_med = re.search(r"med=([\d\.]+m?s?)", line)
            m_max = re.search(r"max=([\d\.]+m?s?)", line)
            m_p90 = re.search(r"p\(90\)=([\d\.]+m?s?)", line)
            m_p95 = re.search(r"p\(95\)=([\d\.]+m?s?)", line)
            m_p99 = re.search(r"p\(99\)=([\d\.]+m?s?)", line)
            
            if m_avg: avg_dur = m_avg.group(1)
            if m_min: min_dur = m_min.group(1)
            if m_med: med_dur = m_med.group(1)
            if m_max: max_dur = m_max.group(1)
            if m_p90: p90_dur = m_p90.group(1)
            if m_p95: p95_dur = m_p95.group(1)
            if m_p99: p99_dur = m_p99.group(1)
            
        elif "http_req_failed" in line:
            m_fail = re.search(r"([\d\.]+)%", line)
            if m_fail: fail_rate = m_fail.group(1) + "%"
        elif "http_reqs" in line:
            m_rps = re.search(r"([\d\.]+)/s", line)
            if m_rps: reqs_per_sec = m_rps.group(1)
            
    if fail_rate == "N/A":
        fail_rate = "0.00%"
            
    results.append({
        "VUs": vus,
        "Duration": duration,
        "RPS": reqs_per_sec,
        "Failure": fail_rate,
        "Avg": avg_dur,
        "Min": min_dur,
        "Med": med_dur,
        "Max": max_dur,
        "p90": p90_dur,
        "p95": p95_dur,
        "p99": p99_dur
    })

# Write markdown report
report = "# Load Test Results per Tier (Detailed)\n\n"
report += "| VUs | Duration | Req/Sec | Failure | Min | Avg | Median | Max | p90 | p95 | p99 |\n"
report += "|-----|----------|---------|---------|-----|-----|--------|-----|-----|-----|-----|\n"
for r in results:
    report += f"| {r['VUs']} | {r['Duration']} | {r['RPS']} | {r['Failure']} | {r['Min']} | {r['Avg']} | {r['Med']} | {r['Max']} | {r['p90']} | {r['p95']} | {r['p99']} |\n"

with open(r"c:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\5cffe2a5-183d-4827-b71a-0cd2beb473a3\detailed_load_test_results.md", "w") as f:
    f.write(report)
    
print("Detailed tests completed and report generated.")
