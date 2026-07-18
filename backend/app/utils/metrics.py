from prometheus_client import Counter

# Metrics for alerting dashboards
ORDER_FAILURES = Counter("sj_order_failures_total", "Total number of failed orders", ["reason"])

PAYMENT_ERRORS = Counter("sj_payment_errors_total", "Total number of payment errors", ["gateway", "error_type"])
