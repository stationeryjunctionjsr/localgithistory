import re
def remove_metrics(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'ORDER_FAILURES\.labels\([^)]*\)\.inc\(\)\s*', '', content)
    content = re.sub(r'PAYMENT_ERRORS\.labels\([^)]*\)\.inc\(\)\s*', '', content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

remove_metrics("app/routers/payments.py")
remove_metrics("app/services/order_service.py")
