# GPS Configuration for Bus Tracking System
# Hackathon-ready GPS mode configuration

# 🚀 QUICK MODE TOGGLE - Change this to switch GPS modes instantly
CURRENT_MODE = "SIMULATOR"  # Options: "SIMULATOR", "MOBILE", "REAL_GPS"

# GPS Source Settings
GPS_SOURCES = {
    'SIMULATOR': {
        'enabled': True,
        'script': 'bus_simulator.py',
        'description': 'Simulated GPS data with predefined routes'
    },
    'MOBILE': {
        'enabled': True,
        'description': 'Live GPS data from mobile device'
    },
    'REAL_GPS': {
        'enabled': False,  # For future real GPS hardware
        'description': 'Real GPS hardware devices in buses'
    }
}

# Mobile GPS Settings - Auto-loaded defaults for fast hackathon setup
MOBILE_GPS_CONFIG = {
    'default_bus_id': 'MOBILE-BUS-001',
    'server_url': 'http://127.0.0.1:8000',  # Change to PC LAN IP when using phone
    'default_speed': 0.0,
    'default_heading': 0.0,
    'update_interval': 5,  # seconds
}

# 📝 HACKATHON NOTES:
# - To use phone GPS: Change server_url to your PC's LAN IP (e.g., 'http://192.168.1.100:8000')
# - To switch modes: Just change CURRENT_MODE above
# - Mobile mode uses consistent bus_id (no random IDs)

def get_current_gps_mode():
    """Get current GPS mode based on CURRENT_MODE setting"""
    return CURRENT_MODE

def get_gps_source_info():
    """Get information about current GPS source"""
    return GPS_SOURCES.get(CURRENT_MODE, {})