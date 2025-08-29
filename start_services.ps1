# Bus Tracking System - Service Startup Script
# This script starts both the Django server and the bus simulator

Write-Host "🚌 Bus Tracking System - Starting Services" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please ensure Python is installed and in your PATH." -ForegroundColor Red
    exit 1
}

# Start Django server in background
Write-Host "`n🔧 Starting Django development server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver", "127.0.0.1:8000" -WindowStyle Minimized

# Wait a bit for Django to start
Start-Sleep -Seconds 3

# Test if Django server is responding
Write-Host "🔍 Testing Django server connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/get_locations/" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Django server is running successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Django server responded but with status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Django server connection failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔄 Waiting 5 more seconds for Django to fully start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Start bus simulator
Write-Host "`n🚌 Starting bus simulator..." -ForegroundColor Yellow
Write-Host "📍 This will simulate 5 buses moving around Delhi" -ForegroundColor Cyan
Write-Host "⏱️ Location updates every 3-7 seconds" -ForegroundColor Cyan
Write-Host "🛑 Press Ctrl+C to stop the simulator when ready" -ForegroundColor Cyan
Write-Host ""

python bus_simulator.py
