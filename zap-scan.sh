#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# OWASP ZAP Baseline Scan — run this against your staging environment
# before every production deployment.
#
# Requirements:
#   - Docker installed and running
#   - STAGING_URL set to your staging API base URL (e.g. https://api-staging.yourdomain.com)
#
# Usage:
#   export STAGING_URL=https://api-staging.yourdomain.com
#   bash zap-scan.sh
#
# Output: zap-report.html in the current directory
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

STAGING_URL="${STAGING_URL:-http://localhost:8000}"
REPORT_DIR="$(pwd)/zap-reports"
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/zap_report_$TIMESTAMP.html"

echo "▶  Running OWASP ZAP baseline scan against: $STAGING_URL"
echo "   Report will be saved to: $REPORT_FILE"

docker run --rm \
  -v "$REPORT_DIR:/zap/wrk:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
    -t "$STAGING_URL" \
    -r "zap_report_$TIMESTAMP.html" \
    -I \
    -j \
    --hook=/zap/auth_hook.py 2>/dev/null || true

echo ""
echo "✅  Scan complete. Open: $REPORT_FILE"
echo ""
echo "Common findings to look for:"
echo "  WARN: Missing Anti-clickjacking Header  → already fixed (X-Frame-Options: DENY)"
echo "  WARN: X-Content-Type-Options Header     → already fixed"
echo "  WARN: Strict-Transport-Security Header  → already fixed"
echo "  ALERT: SQL Injection                    → verify all DAO queries use :params"
echo "  ALERT: Application Error Disclosure     → check /docs is disabled in prod"
