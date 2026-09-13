import subprocess
import re
import os
import sys

def main():
    print("=== Forensic Scan: Routers & Models Diff ===")
    diff = subprocess.check_output(['git', 'diff', 'backend/app/routers/', 'backend/app/models/'], text=True)
    added_lines = [line[1:] for line in diff.splitlines() if line.startswith('+') and not line.startswith('+++')]

    patterns = [
        ("hardcoded_return", re.compile(r'return\s+[\'"](?:PASS|test|fake|dummy|mock)[\'"]', re.I)),
        ("test_conditional", re.compile(r'if\s+.*(?:test|mock).*:\s*return', re.I)),
        ("not_implemented", re.compile(r'raise\s+NotImplementedError', re.I)),
        ("pass_validator", re.compile(r'def\s+validate_.*\(.*\):\s*pass', re.I)),
        ("dummy_validator", re.compile(r'def\s+.*validator.*:\s*return\s+(?:True|None|v)', re.I)),
    ]

    findings = []
    for line in added_lines:
        for name, pat in patterns:
            if pat.search(line):
                findings.append((name, line.strip()))

    print(f"Total added lines analyzed: {len(added_lines)}")
    print(f"Suspicious pattern matches: {len(findings)}")
    for name, line in findings:
        print(f"  [{name}] {line}")

if __name__ == "__main__":
    main()
