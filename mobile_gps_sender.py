#!/usr/bin/env python3
"""
Mobile GPS Sender for Bus Tracking System
🚀 Hackathon-ready: Auto-loads defaults, minimal setup required
Sends live GPS data from mobile device to the backend API
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gps_config import MOBILE_GPS_CONFIG

class MobileGPSSender:
    def __init__(self, server_url=None, bus_id=None):
        # 🚀 Auto-load defaults from config for fast hackathon setup
        self.server_url = server_url or MOBILE_GPS_CONFIG['server_url']
        self.bus_id = bus_id or MOBILE_GPS_CONFIG['default_bus_id']
        self.update_interval = MOBILE_GPS_CONFIG['update_interval']
        self.running = False
        
    def send_gps_data(self, latitude, longitude, speed=0.0, heading=0.0):
        """Send GPS data to the backend API"""
        url = f"{self.server_url}/api/update_location/"
        data = {
            'bus_id': self.bus_id,
            'latitude': float(latitude),
            'longitude': float(longitude),
            'speed': float(speed),
            'heading': float(heading)
        }
        
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(data), headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ GPS data sent: ({latitude:.6f}, {longitude:.6f}) - Speed: {speed:.1f}km/h")
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 Connection error - Is the Django server running?")
            return False
        except requests.exceptions.Timeout:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ Request timeout")
            return False
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")
            return False
    
    def test_connection(self):
        """Test connection to Django server"""
        print("🔍 Testing connection to Django server...")
        try:
            response = requests.get(f"{self.server_url}/api/get_locations/", timeout=5)
            if response.status_code == 200:
                print("✅ Connection successful!")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\nMake sure to:")
            print("1. Run 'python manage.py runserver' in another terminal")
            print("2. Ensure the server is running on http://127.0.0.1:8000")
            return False
    
    def manual_mode(self):
        """📱 Manual GPS input mode for testing"""
        print("📱 Mobile GPS Sender - Manual Mode")
        print("==================================")
        print(f"Bus ID: {self.bus_id} (consistent for mobile mode)")
        print(f"Server: {self.server_url}")
        print("\nEnter GPS coordinates manually (or 'quit' to exit):")
        
        while True:
            try:
                print("\n" + "="*50)
                lat_input = input("Enter Latitude (or 'quit'): ").strip()
                if lat_input.lower() == 'quit':
                    break
                
                lng_input = input("Enter Longitude: ").strip()
                speed_input = input("Enter Speed (km/h, optional): ").strip()
                heading_input = input("Enter Heading (degrees, optional): ").strip()
                
                latitude = float(lat_input)
                longitude = float(lng_input)
                speed = float(speed_input) if speed_input else 0.0
                heading = float(heading_input) if heading_input else 0.0
                
                success = self.send_gps_data(latitude, longitude, speed, heading)
                if success:
                    print("✅ Data sent successfully!")
                else:
                    print("❌ Failed to send data")
                    
            except ValueError:
                print("❌ Invalid input. Please enter valid numbers.")
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                break
    
    def auto_mode_with_input(self):
        """🚀 Auto mode with single GPS input that repeats - hackathon optimized"""
        print("📱 Mobile GPS Sender - Auto Mode")
        print("================================")
        print(f"Bus ID: {self.bus_id} (consistent for mobile mode)")
        print(f"Server: {self.server_url}")
        print(f"Update interval: {self.update_interval} seconds")
        
        try:
            latitude = float(input("Enter your current Latitude: "))
            longitude = float(input("Enter your current Longitude: "))
            speed = float(input("Enter Speed (km/h, optional): ") or "0")
            heading = float(input("Enter Heading (degrees, optional): ") or "0")
            
            print(f"\n🚀 Starting auto mode with coordinates: ({latitude:.6f}, {longitude:.6f})")
            print("📝 Using consistent bus_id for mobile GPS mode (no random IDs)")
            print("Press Ctrl+C to stop\n")
            
            self.running = True
            while self.running:
                success = self.send_gps_data(latitude, longitude, speed, heading)
                if not success:
                    print("⚠️ Failed to send data, retrying...")
                
                time.sleep(self.update_interval)
                
        except ValueError:
            print("❌ Invalid input. Please enter valid numbers.")
        except KeyboardInterrupt:
            print("\n🛑 Stopping auto mode...")
            self.running = False

def main():
    """🚀 Hackathon-ready main function with auto-loaded defaults"""
    print("📱 Mobile GPS Sender for Bus Tracking")
    print("====================================")
    
    # 🚀 Auto-load defaults for fast setup
    default_server = MOBILE_GPS_CONFIG['server_url']
    default_bus_id = MOBILE_GPS_CONFIG['default_bus_id']
    
    print(f"🚀 Quick Start Mode - Using defaults:")
    print(f"   Server: {default_server}")
    print(f"   Bus ID: {default_bus_id}")
    print(f"\n📝 Note: If using phone, change server_url in gps_config.py to your PC's LAN IP")
    
    # Ask if user wants to override defaults
    override = input("\nUse defaults? (y/n, default=y): ").strip().lower()
    
    if override == 'n':
        server_url = input(f"Enter server URL (default: {default_server}): ").strip()
        if not server_url:
            server_url = default_server
        
        bus_id = input(f"Enter Bus ID (default: {default_bus_id}): ").strip()
        if not bus_id:
            bus_id = default_bus_id
    else:
        server_url = default_server
        bus_id = default_bus_id
    
    sender = MobileGPSSender(server_url, bus_id)
    
    # Test connection first
    if not sender.test_connection():
        print("\n❌ Cannot connect to server. Please check your Django server.")
        print("📝 Tip: If using phone, make sure server_url points to your PC's LAN IP")
        return
    
    print("\nSelect mode:")
    print("1. Manual Mode (Enter GPS coordinates manually)")
    print("2. Auto Mode (Enter coordinates once, send repeatedly)")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            sender.manual_mode()
        elif choice == '2':
            sender.auto_mode_with_input()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()