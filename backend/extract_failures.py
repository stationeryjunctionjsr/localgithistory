import re

log_path = r"C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\d87d9ce7-79ea-4843-900e-eacac0995ba9\.system_generated\tasks\task-25389.log"

with open(log_path, 'r', encoding='utf-8') as f:
    log_content = f.read()

# Split log by "__________________________ test_" to get individual test failures
test_blocks = log_content.split("__________________________ test_")[1:]

failures = []
for block in test_blocks:
    test_name = block.split()[0]
    
    # Extract the error type/message. Usually it's the last few lines before "------------------------------ Captured"
    # or the lines starting with "E   "
    error_lines = []
    for line in block.split('\n'):
        if line.startswith('E   '):
            error_lines.append(line)
            
    if error_lines:
        failures.append(f"Test: {test_name}\nError: " + "\n".join(error_lines[:5]) + "\n")
    else:
        # if no "E   " lines, find the last exception line
        exception_lines = re.findall(r'(\w+Error: .*?)(?=\n|$)', block)
        if exception_lines:
            failures.append(f"Test: {test_name}\nError: {exception_lines[-1]}\n")

with open("test_failures_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(failures))

print(f"Extracted {len(failures)} failures.")
