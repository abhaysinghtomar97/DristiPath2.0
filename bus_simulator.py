import requests
import time
import json
import random
import math
from datetime import datetime
from threading import Thread

# Enhanced bus routes with more realistic city coverage
BUS_ROUTES = {
    'BUS-001': {
        'name': 'Central Delhi Express',
        'route': [
            (28.6139, 77.2090),  # India Gate
            (28.6289, 77.2065),  # Connaught Place  
            (28.6448, 77.2167),  # Karol Bagh
            (28.6562, 77.2410),  # Rohini Sector 3
            (28.6692, 77.2285),  # Pitampura
            (28.6448, 77.2167),  # Return - Karol Bagh
            (28.6289, 77.2065),  # Return - Connaught Place
            (28.6139, 77.2090),  # Return - India Gate
        ],
        'speed_range': (15, 45)  # km/h
    },
    'BUS-002': {
        'name': 'South Delhi Route',
        'route': [
            (28.5355, 77.3910),  # Noida Sector 18
            (28.5244, 77.1855),  # Lajpat Nagar
            (28.5535, 77.2588),  # Safdarjung
            (28.6139, 77.2090),  # India Gate
            (28.6289, 77.2065),  # Connaught Place
            (28.5535, 77.2588),  # Return - Safdarjung
            (28.5244, 77.1855),  # Return - Lajpat Nagar
            (28.5355, 77.3910),  # Return - Noida
        ],
        'speed_range': (20, 50)
    },
    'BUS-003': {
        'name': 'North Delhi Circular',
        'route': [
            (28.7041, 77.1025),  # Delhi University
            (28.6562, 77.2410),  # Rohini
            (28.6923, 77.1756),  # Azadpur
            (28.6448, 77.2167),  # Karol Bagh
            (28.6289, 77.2065),  # Connaught Place
            (28.6139, 77.2090),  # India Gate
            (28.6289, 77.2065),  # Return - CP
            (28.6448, 77.2167),  # Return - Karol Bagh
            (28.6923, 77.1756),  # Return - Azadpur
            (28.6562, 77.2410),  # Return - Rohini
            (28.7041, 77.1025),  # Return - DU
        ],
        'speed_range': (10, 40)
    },
    'BUS-004': {
        'name': 'Airport Express',
        'route': [
            (28.5562, 77.1000),  # IGI Airport Terminal 3
            (28.5355, 77.3910),  # Noida Sector 18
            (28.6139, 77.2090),  # India Gate
            (28.6289, 77.2065),  # Connaught Place
            (28.6448, 77.2167),  # Karol Bagh
            (28.6289, 77.2065),  # Return - CP
            (28.6139, 77.2090),  # Return - India Gate
            (28.5355, 77.3910),  # Return - Noida
            (28.5562, 77.1000),  # Return - Airport
        ],
        'speed_range': (25, 60)
    },
    'BUS-005': {
        'name': 'East Delhi Connect',
        'route': [
            (28.6507, 77.2334),  # Rajouri Garden
            (28.6448, 77.2167),  # Karol Bagh
            (28.6289, 77.2065),  # Connaught Place
            (28.6139, 77.2090),  # India Gate
            (28.5244, 77.1855),  # Lajpat Nagar
            (28.6139, 77.2090),  # Return - India Gate
            (28.6289, 77.2065),  # Return - CP
            (28.6448, 77.2167),  # Return - Karol Bagh
            (28.6507, 77.2334),  # Return - Rajouri Garden
        ],
        'speed_range': (12, 35)
    }
}

class BusSimulator:
    def __init__(self, server_url='http://localhost:8000'):
        self.server_url = server_url
        self.bus_states = {}
        self.running = False
        
        # Initialize bus states with more realistic data
        for bus_id, route_info in BUS_ROUTES.items():
            self.bus_states[bus_id] = {
                'position_index': random.randint(0, len(route_info['route']) - 1),
                'current_speed': random.randint(*route_info['speed_range']),
                'heading': random.randint(0, 360),
                'last_update': time.time(),
                'route_info': route_info,
                # Add slight position variation for realism
                'position_offset': (random.uniform(-0.001, 0.001), random.uniform(-0.001, 0.001))
            }
    
    def calculate_heading(self, from_pos, to_pos):
        """Calculate heading between two GPS coordinates"""
        lat1, lon1 = from_pos
        lat2, lon2 = to_pos
        
        dlon = math.radians(lon2 - lon1)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def add_realistic_variation(self, lat, lon, bus_id):
        """Add small realistic GPS variations"""
        offset = self.bus_states[bus_id]['position_offset']
        # Small random variation to simulate GPS drift
        variation_lat = random.uniform(-0.0005, 0.0005) + offset[0]
        variation_lon = random.uniform(-0.0005, 0.0005) + offset[1]
        
        return lat + variation_lat, lon + variation_lon
    
    def send_location_update(self, bus_id, latitude, longitude, speed=0, heading=0):
        """Send enhanced location update to the Django API"""
        url = f"{self.server_url}/api/update_location/"
        data = {
            'bus_id': bus_id,
            'latitude': latitude,
            'longitude': longitude,
            'speed': speed,
            'heading': heading
        }
        
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(data), headers=headers, timeout=5)
            
            if response.status_code == 200:
                route_name = self.bus_states[bus_id]['route_info']['name']
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {bus_id} ({route_name}): ({latitude:.4f}, {longitude:.4f}) - Speed: {speed:.1f}km/h")
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error updating {bus_id}: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ Timeout updating {bus_id}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 Connection error - Is the Django server running?")
            return False
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error updating {bus_id}: {e}")
            return False
    
    def simulate_single_bus(self, bus_id):
        """Simulate movement for a single bus"""
        bus_state = self.bus_states[bus_id]
        route_info = bus_state['route_info']
        route_points = route_info['route']
        speed_range = route_info['speed_range']
        
        while self.running:
            try:
                current_index = bus_state['position_index']
                next_index = (current_index + 1) % len(route_points)
                
                # Get current and next positions
                current_pos = route_points[current_index]
                next_pos = route_points[next_index]
                
                # Add realistic GPS variation
                varied_pos = self.add_realistic_variation(*current_pos, bus_id)
                
                # Calculate heading to next point
                heading = self.calculate_heading(current_pos, next_pos)
                bus_state['heading'] = heading
                
                # Vary speed realistically
                if random.random() < 0.3:  # 30% chance to change speed
                    bus_state['current_speed'] = random.randint(*speed_range)
                
                # Send location update
                success = self.send_location_update(
                    bus_id, 
                    varied_pos[0], 
                    varied_pos[1], 
                    bus_state['current_speed'],
                    bus_state['heading']
                )
                
                if success:
                    # Move to next position
                    bus_state['position_index'] = next_index
                    bus_state['last_update'] = time.time()
                
                # Different buses move at different intervals for realism
                sleep_time = random.uniform(3, 7)  # 3-7 seconds
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error in {bus_id} simulation: {e}")
                time.sleep(5)  # Wait before retrying
    
    def simulate_movement(self):
        """Start simulation with all buses running in separate threads"""
        print("🚌 Enhanced Bus Tracking Simulator")
        print("===================================")
        print(f"Simulating {len(BUS_ROUTES)} buses:")
        for bus_id, route_info in BUS_ROUTES.items():
            print(f"  - {bus_id}: {route_info['name']}")
        print("\nMake sure your Django server is running on http://localhost:8000")
        print("Press Ctrl+C to stop the simulation\n")
        
        self.running = True
        threads = []
        
        # Start a thread for each bus
        for bus_id in BUS_ROUTES:
            thread = Thread(target=self.simulate_single_bus, args=(bus_id,), daemon=True)
            thread.start()
            threads.append(thread)
            print(f"✅ Started simulation for {bus_id}")
            time.sleep(1)  # Stagger the starts
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
                # Periodically show status
                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    alive_threads = sum(1 for t in threads if t.is_alive())
                    print(f"\n📊 Status: {alive_threads}/{len(threads)} buses active")
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping simulation...")
            self.running = False
            
            # Wait for threads to finish
            for thread in threads:
                thread.join(timeout=2)
            
            print("✅ Bus simulation stopped.")
    
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
            print("2. Ensure the server is running on http://localhost:8000")
            return False

if __name__ == "__main__":
    simulator = BusSimulator()
    simulator.simulate_movement()
