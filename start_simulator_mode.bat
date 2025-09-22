@echo off
echo 🚌 Starting Bus Tracking in SIMULATOR Mode
echo ==========================================

echo Setting GPS mode to SIMULATOR...
python -c "
import re
with open('gps_config.py', 'r') as f:
    content = f.read()
content = re.sub(r'USE_SIMULATOR = False', 'USE_SIMULATOR = True', content)
with open('gps_config.py', 'w') as f:
    f.write(content)
print('✅ GPS mode set to SIMULATOR')
"

echo.
echo Starting Django server in background...
start "Django Server" cmd /k "python manage.py runserver"

echo.
echo Waiting 3 seconds for server to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting Bus Simulator...
python bus_simulator.py

pause