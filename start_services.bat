@echo off
echo 🚌 Bus Tracking System - Starting Services
echo ==========================================

echo.
echo 🔧 Starting Django development server...
start /min python manage.py runserver 127.0.0.1:8000

echo ⏱️ Waiting for Django server to start...
timeout /t 5 /nobreak > nul

echo.
echo 🚌 Starting bus simulator...
echo 📍 This will simulate 5 buses moving around Delhi
echo ⏱️ Location updates every 3-7 seconds
echo 🛑 Press Ctrl+C to stop the simulator when ready
echo.

python bus_simulator.py

pause
