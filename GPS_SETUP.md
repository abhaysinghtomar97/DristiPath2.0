# 📱 GPS Mode Setup Guide

## Quick Start

### Option 1: Use Batch Scripts (Easiest)
- **Simulator Mode**: Double-click `start_simulator_mode.bat`
- **Mobile GPS Mode**: Double-click `start_mobile_mode.bat`

### Option 2: Use GPS Manager
```bash
python gps_manager.py
```

### Option 3: Manual Setup

#### Simulator Mode
1. Set `USE_SIMULATOR = True` in `gps_config.py`
2. Run: `python manage.py runserver`
3. Run: `python bus_simulator.py`

#### Mobile GPS Mode
1. Set `USE_SIMULATOR = False` in `gps_config.py`
2. Run: `python manage.py runserver`
3. Run: `python mobile_gps_sender.py`

## Mobile GPS Options

### Python Script (Recommended)
```bash
python mobile_gps_sender.py
```
- Manual mode: Enter GPS coordinates manually
- Auto mode: Enter once, sends repeatedly

### Web Interface
Open `mobile_gps_web.html` in your mobile browser for GUI interface.

## API Endpoint
Both modes send data to: `POST /api/update_location/`

JSON format:
```json
{
  "bus_id": "MOBILE-BUS-001",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "speed": 0.0,
  "heading": 0.0
}
```

## Configuration
Edit `gps_config.py` to change:
- `USE_SIMULATOR`: Toggle between modes
- `MOBILE_GPS_CONFIG`: Default bus ID, update interval
- Bus IDs and other settings