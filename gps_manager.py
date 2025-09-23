#!/usr/bin/env python3
"""
GPS Manager for Bus Tracking System
Easy way to switch between GPS modes and start appropriate services
"""

import os
import sys
import subprocess
from gps_config import USE_SIMULATOR, get_current_gps_mode, get_gps_source_info

def show_current_status():
    """Show current GPS configuration status"""
    mode = get_current_gps_mode()
    info = get_gps_source_info()
    
    print("🚌 Bus Tracking GPS Manager")
    print("=" * 40)
    print(f"Current Mode: {mode}")
    print(f"Description: {info.get('description', 'Unknown')}")
    print(f"USE_SIMULATOR: {USE_SIMULATOR}")
    print("=" * 40)

def toggle_gps_mode():
    """Toggle between simulator and mobile GPS modes"""
    config_file = "gps_config.py"
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Toggle the setting
        if "USE_SIMULATOR = True" in content:
            new_content = content.replace("USE_SIMULATOR = True", "USE_SIMULATOR = False")
            new_mode = "MOBILE"
        else:
            new_content = content.replace("USE_SIMULATOR = False", "USE_SIMULATOR = True")
            new_mode = "SIMULATOR"
        
        # Write back
        with open(config_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ GPS mode switched to: {new_mode}")
        return True
        
    except Exception as e:
        print(f"❌ Error toggling GPS mode: {e}")
        return False

def start_simulator():
    """Start the bus simulator"""
    print("🚀 Starting Bus Simulator...")
    try:
        subprocess.run([sys.executable, "bus_simulator.py"])
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped")
    except Exception as e:
        print(f"❌ Error starting simulator: {e}")

def start_mobile_gps():
    """Start the mobile GPS sender"""
    print("📱 Starting Mobile GPS Sender...")
    try:
        subprocess.run([sys.executable, "mobile_gps_sender.py"])
    except KeyboardInterrupt:
        print("\n🛑 Mobile GPS sender stopped")
    except Exception as e:
        print(f"❌ Error starting mobile GPS sender: {e}")

def start_django_server():
    """Start Django development server"""
    print("🌐 Starting Django Server...")
    try:
        subprocess.run([sys.executable, "manage.py", "runserver"])
    except KeyboardInterrupt:
        print("\n🛑 Django server stopped")
    except Exception as e:
        print(f"❌ Error starting Django server: {e}")

def main():
    """Main menu"""
    while True:
        print("\n")
        show_current_status()
        print("\nOptions:")
        print("1. Toggle GPS Mode (Simulator ↔ Mobile)")
        print("2. Start Current GPS Source")
        print("3. Start Django Server")
        print("4. Start Bus Simulator (Force)")
        print("5. Start Mobile GPS Sender (Force)")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            toggle_gps_mode()
            # Reload the config
            import importlib
            import gps_config
            importlib.reload(gps_config)
            
        elif choice == '2':
            current_mode = get_current_gps_mode()
            if current_mode == 'SIMULATOR':
                start_simulator()
            elif current_mode == 'MOBILE':
                start_mobile_gps()
            else:
                print("❌ Unknown GPS mode")
                
        elif choice == '3':
            start_django_server()
            
        elif choice == '4':
            start_simulator()
            
        elif choice == '5':
            start_mobile_gps()
            
        elif choice == '6':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()