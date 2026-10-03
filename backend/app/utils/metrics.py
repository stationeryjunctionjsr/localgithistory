# ANA-6 / SEC-3: The Prometheus counters (ORDER_FAILURES, PAYMENT_ERRORS) and
# the /metrics endpoint have been removed because:
#   1. The /metrics endpoint was disabled (commented out in main.py) due to
#      latency overhead from the Instrumentator middleware.
#   2. The counters were never incremented anywhere in the codebase, so they
#      provided no actual observability benefit while consuming memory.
#
# To re-enable Prometheus metrics:
#   1. Uncomment PrometheusInstrumentator in main.py and add an IP-allowlist
#      reverse-proxy rule so /metrics is never publicly reachable.
#   2. Re-add counters here and instrument the order/payment failure paths.
#   3. Add to requirements: prometheus-client, prometheus-fastapi-instrumentator
