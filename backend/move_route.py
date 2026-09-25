with open('app/routers/orders.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if '@router.get("/{order_id}", response_model=PopulatedOrderResponse)' in line:
        start_idx = i
    if start_idx != -1 and i > start_idx and '@router.post("", response_model=PopulatedOrderResponse' in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    chunk = lines[start_idx:end_idx]
    del lines[start_idx:end_idx]
    lines.extend(chunk)
    with open('app/routers/orders.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Moved get_order to the end")
