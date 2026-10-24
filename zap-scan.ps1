# ─────────────────────────────────────────────────────────────────────────────
# OWASP ZAP Baseline Scan (PowerShell) — run against staging before each deploy
#
# Requirements: Docker Desktop installed and running
# Usage: .\zap-scan.ps1 -StagingUrl https://api-staging.yourdomain.com
# ─────────────────────────────────────────────────────────────────────────────
param(
    [string]$StagingUrl = "http://localhost:8000"
)

$ReportDir = Join-Path (Get-Location) "zap-reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportFile = "zap_report_$Timestamp.html"

Write-Host "▶  Running OWASP ZAP baseline scan against: $StagingUrl"
Write-Host "   Report will be saved to: $ReportDir\$ReportFile"

docker run --rm `
    -v "${ReportDir}:/zap/wrk:rw" `
    ghcr.io/zaproxy/zaproxy:stable `
    zap-baseline.py `
    -t $StagingUrl `
    -r $ReportFile `
    -I

Write-Host ""
Write-Host "✅  Scan complete. Open: $ReportDir\$ReportFile"
