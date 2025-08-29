# Simple Bus Tracking System Startup Script

Write-Host "Bus Tracking System - Starting Services" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Step 1: Kill existing Python processes
Write-Host "`nCleaning up existing processes..." -ForegroundColor Yellow
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Step 2: Start Django server
Write-Host "`nStarting Django development server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver", "127.0.0.1:8000" -WindowStyle Hidden

# Step 3: Wait for server to start
Write-Host "Waiting for Django server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Step 4: Test server connection
Write-Host "Testing server connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/get_locations/" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "SUCCESS: Django server is running!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Django server responded with status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: Django server connection failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 5: Test admin login
Write-Host "`nTesting admin login functionality..." -ForegroundColor Yellow
try {
    $loginData = @{ username = "admin"; password = "admin123" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/admin/login/" -Method POST -Body $loginData -ContentType "application/json" -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    
    if ($result.status -eq "success") {
        Write-Host "SUCCESS: Admin login working!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Admin login failed" -ForegroundColor Red
    }
} catch {
    Write-Host "ERROR: Admin login test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Start bus simulator
Write-Host "`nStarting bus simulator..." -ForegroundColor Yellow
Write-Host "This will simulate 5 buses moving around Delhi" -ForegroundColor Cyan
Write-Host "Location updates every 3-7 seconds" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the simulator when ready" -ForegroundColor Cyan
Write-Host ""

# Test simulator connection first
python -c "from bus_simulator import BusSimulator; sim = BusSimulator(); sim.test_connection()"

# Start the actual simulator
python bus_simulator.py
