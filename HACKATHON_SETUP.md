# 🚀 Hackathon Quick Setup Guide

## GPS Mode Toggle (Instant Switch)

**File:** `gps_config.py`
```python
CURRENT_MODE = "SIMULATOR"  # Change to: "MOBILE" or "REAL_GPS"
```

## Mobile GPS Setup

### 1. For Local Testing (Same Device)
- Keep default: `server_url: 'http://127.0.0.1:8000'`
- Run: `python mobile_gps_sender.py`

### 2. For Phone GPS (Different Device)
- Find your PC's LAN IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
- Update `gps_config.py`:
```python
MOBILE_GPS_CONFIG = {
    'server_url': 'http://192.168.1.100:8000',  # Your PC's IP
    # ... rest stays same
}
```

## Quick Start Commands

```bash
# Terminal 1: Start Django server
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Choose GPS mode
# For simulator:
python bus_simulator.py

# For mobile GPS:
python mobile_gps_sender.py
```

## Mode Switching

1. **Simulator Mode**: Set `CURRENT_MODE = "SIMULATOR"`
2. **Mobile Mode**: Set `CURRENT_MODE = "MOBILE"`
3. **Real GPS**: Set `CURRENT_MODE = "REAL_GPS"` (future)

## Key Features

- ✅ Auto-loaded defaults (minimal typing)
- ✅ Consistent bus_id for mobile mode
- ✅ Fast mode switching
- ✅ All backend APIs unchanged
- ✅ Menu options for flexibility

## Troubleshooting

- **Connection failed**: Check Django server is running
- **Phone can't connect**: Use PC's LAN IP in server_url
- **Mode not working**: Check CURRENT_MODE in gps_config.py