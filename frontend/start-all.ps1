# start-all.ps1
# Check if backend is already running on port 8000
$backendConn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if (-not $backendConn) {
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
} else {
    Write-Host "Backend API is already running on port 8000." -ForegroundColor Green
}

# Check if frontend is already running on port 3000
$frontendConn = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if (-not $frontendConn) {
    Write-Host "Starting Frontend..."
    npm run dev
} else {
    Write-Host "Frontend dev server is already running on port 3000." -ForegroundColor Green
}

