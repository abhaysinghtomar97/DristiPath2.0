@echo off
echo 📱 Starting Bus Tracking in MOBILE GPS Mode
echo ==========================================

echo Setting GPS mode to MOBILE...
python -c "
import re
with open('gps_config.py', 'r') as f:
    content = f.read()
content = re.sub(r'USE_SIMULATOR = True', 'USE_SIMULATOR = False', content)
with open('gps_config.py', 'w') as f:
    f.write(content)
print('✅ GPS mode set to MOBILE')
"

echo.
echo Starting Django server in background...
start "Django Server" cmd /k "python manage.py runserver"

echo.
echo Waiting 3 seconds for server to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting Mobile GPS Sender...
python mobile_gps_sender.py

pause