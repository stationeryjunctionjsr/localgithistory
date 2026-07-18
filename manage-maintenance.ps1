# manage-maintenance.ps1
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet('on', 'off')]
    [string]$Action
)

$envPath = "c:\Ecommerce app\backend\.env"
if (-not (Test-Path $envPath)) {
    Write-Error "Could not find .env file at $envPath"
    exit 1
}

# 1. Update the .env file content
$content = Get-Content $envPath -Raw
if ($Action -eq 'on') {
    if ($content -match "MAINTENANCE_MODE=") {
        $content = $content -replace "MAINTENANCE_MODE=\w+", "MAINTENANCE_MODE=true"
    } else {
        $content += "`r`nMAINTENANCE_MODE=true"
    }
    Write-Host "Activating Maintenance Mode in .env..." -ForegroundColor Yellow
} else {
    if ($content -match "MAINTENANCE_MODE=") {
        $content = $content -replace "MAINTENANCE_MODE=\w+", "MAINTENANCE_MODE=false"
    } else {
        $content += "`r`nMAINTENANCE_MODE=false"
    }
    Write-Host "Deactivating Maintenance Mode in .env..." -ForegroundColor Green
}
Set-Content $envPath $content -NoNewline

# 2. Restart the backend process to pick up the change
Write-Host "Restarting Backend API Server to apply changes..." -ForegroundColor Cyan

# Find process on port 8000
$connection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connection) {
    foreach ($procId in $connection.OwningProcess) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc -and ($proc.ProcessName -eq 'python' -or $proc.ProcessName -eq 'node')) {
            Write-Host "Stopping process $($proc.ProcessName) (PID: $procId)..."
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

# Find other python instances running app.main
$pyProcs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -match "app.main" -or $_.CommandLine -match "run.py" }
foreach ($p in $pyProcs) {
    Write-Host "Stopping background python process (PID: $($p.ProcessId))..."
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

# Start backend
cd "c:\Ecommerce app\backend"
Start-Process python -ArgumentList "-m app.main" -NoNewWindow

# Wait for backend to start
Write-Host "Waiting for Backend API to start on port 8000..." -ForegroundColor Cyan
$started = $false
for ($i = 0; $i -lt 30; $i++) {
    $conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($conn) {
        $started = $true
        break
    }
    Start-Sleep -Seconds 1
}

if ($started) {
    Write-Host "Backend API Server started and listening successfully!" -ForegroundColor Green
} else {
    Write-Warning "Backend API Server started in background but is taking longer to respond on port 8000."
}
