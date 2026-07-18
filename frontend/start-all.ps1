# start-all.ps1
# Start backend
Write-Host "Starting Backend..."
cd ../backend
Start-Process python -ArgumentList "-m app.main" -NoNewWindow
cd ../frontend

# Wait for backend to start
Write-Host "Waiting for Backend API to start on port 8000..."
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
    Write-Host "Backend API is up and running on port 8000!" -ForegroundColor Green
} else {
    Write-Warning "Backend API did not start on port 8000 within 30 seconds."
}

# Start frontend
Write-Host "Starting Frontend..."
npm run dev

