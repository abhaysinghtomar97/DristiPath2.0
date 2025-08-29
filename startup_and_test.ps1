# Complete Bus Tracking System Startup and Test Script
param(
    [switch]$SkipServerStart,
    [switch]$TestOnly
)

Write-Host "🚌 Bus Tracking System - Complete Startup & Test" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Function to test server connection
function Test-DjangoServer {
    param($Url = "http://127.0.0.1:8000")
    try {
        $response = Invoke-WebRequest -Uri "$Url/api/get_locations/" -TimeoutSec 5 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Function to get bus status
function Get-BusStatus {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/get_locations/" -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        
        Write-Host "`n🚌 Current Bus Status:" -ForegroundColor Cyan
        Write-Host "=====================" -ForegroundColor Cyan
        Write-Host "Total active buses: $($data.count)"
        
        foreach ($bus in $data.locations) {
            $lastUpdate = [DateTime]::Parse($bus.last_updated)
            $timeDiff = ((Get-Date) - $lastUpdate).TotalSeconds
            $status = if ($timeDiff -lt 30) { "🟢 ONLINE" } else { "🔴 OFFLINE" }
            Write-Host "  $status $($bus.bus_id) - $($bus.route_name) - Updated $([math]::Round($timeDiff, 1))s ago"
        }
        
        $onlineCount = ($data.locations | Where-Object { 
            $lastUpdate = [DateTime]::Parse($_.last_updated)
            ((Get-Date) - $lastUpdate).TotalSeconds -lt 30 
        }).Count
        
        Write-Host "`n📊 Summary: $onlineCount online / $($data.count) total buses" -ForegroundColor Yellow
        return $onlineCount
    } catch {
        Write-Host "❌ Error checking bus status: $($_.Exception.Message)" -ForegroundColor Red
        return 0
    }
}

if (-not $TestOnly) {
    # Step 1: Kill any existing Python processes
    Write-Host "`n🧹 Cleaning up existing processes..." -ForegroundColor Yellow
    Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    # Step 2: Start Django server
    if (-not $SkipServerStart) {
        Write-Host "`n🔧 Starting Django development server..." -ForegroundColor Yellow
        $djangoProcess = Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver", "127.0.0.1:8000" -PassThru
        
        Write-Host "⏱️ Waiting for Django server to start..." -ForegroundColor Yellow
        $attempts = 0
        $maxAttempts = 15
        
        do {
            Start-Sleep -Seconds 2
            $attempts++
            $serverRunning = Test-DjangoServer
            if ($serverRunning) {
                Write-Host "✅ Django server is running successfully!" -ForegroundColor Green
                break
            } else {
                Write-Host "." -NoNewline
            }
        } while ($attempts -lt $maxAttempts)
        
        if (-not $serverRunning) {
            Write-Host "`n❌ Django server failed to start after $maxAttempts attempts" -ForegroundColor Red
            exit 1
        }
    }
}

# Step 3: Test current status
Write-Host "`n🔍 Testing current system status..." -ForegroundColor Yellow
$onlineCount = Get-BusStatus

# Step 4: Test admin login
Write-Host "`n🔐 Testing admin login functionality..." -ForegroundColor Yellow
try {
    $loginData = @{ username = "admin"; password = "admin123" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/admin/login/" -Method POST -Body $loginData -ContentType "application/json" -UseBasicParsing -SessionVariable session
    $result = $response.Content | ConvertFrom-Json
    
    if ($result.status -eq "success") {
        Write-Host "✅ Admin login successful!" -ForegroundColor Green
        
        # Test admin dashboard access
        try {
            $dashboardResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/admin_panel/" -UseBasicParsing -WebSession $session
            if ($dashboardResponse.StatusCode -eq 200 -and $dashboardResponse.Content -match "Admin Dashboard") {
                Write-Host "✅ Admin dashboard is accessible!" -ForegroundColor Green
            } else {
                Write-Host "⚠️ Admin dashboard responded but content unexpected" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "❌ Admin dashboard access failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Admin login failed: $($result.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Admin login test failed: $($_.Exception.Message)" -ForegroundColor Red
}

if (-not $TestOnly) {
    # Step 5: Start bus simulator if buses are offline
    if ($onlineCount -eq 0) {
        Write-Host "`n🚌 Starting bus simulator (buses are currently offline)..." -ForegroundColor Yellow
        Write-Host "📍 This will simulate 5 buses moving around Delhi" -ForegroundColor Cyan
        Write-Host "⏱️ Location updates every 3-7 seconds" -ForegroundColor Cyan
        Write-Host "🛑 Press Ctrl+C to stop the simulator" -ForegroundColor Cyan
        Write-Host ""
        
        # Test connection first
        $simulator = python -c "
from bus_simulator import BusSimulator
sim = BusSimulator()
if sim.test_connection():
    print('Connection test passed, starting simulation...')
else:
    print('Connection test failed!')
"
        
        # Start the actual simulator
        python bus_simulator.py
    } else {
        Write-Host "`n✅ Some buses are already online ($onlineCount buses)" -ForegroundColor Green
        Write-Host "You can start additional bus simulation with: python bus_simulator.py" -ForegroundColor Cyan
    }
}

Write-Host "`n🎯 System Status Summary:" -ForegroundColor Magenta
Write-Host "========================" -ForegroundColor Magenta
Write-Host "📱 Main page: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "🛠️ Admin panel: http://127.0.0.1:8000/admin_panel/" -ForegroundColor Cyan
Write-Host "🔧 Django admin: http://127.0.0.1:8000/admin/" -ForegroundColor Cyan
Write-Host "🔐 Admin credentials: username=admin, password=admin123" -ForegroundColor Yellow
Write-Host ""
