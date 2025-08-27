<<<<<<< HEAD
Public Crowed Management Bases
=======
# 🚌 Bus Tracking System

A comprehensive real-time bus tracking system built with Django and featuring user location detection, nearest bus finding, bus search functionality, and admin management.

## ✨ Features

### For Users
- **Real-time Bus Tracking**: View live bus locations on an interactive map
- **User Location Detection**: Use your current location to find nearby buses
- **Nearest Bus Finder**: Find buses within a customizable radius
- **Bus Search System**: Search buses by number, route, or destination
- **Responsive Web Interface**: Works on desktop and mobile devices

### For Administrators
- **Admin Dashboard**: Manage buses, routes, and view system statistics
- **Django Admin Interface**: Full backend management capabilities  
- **Bus Management**: Add, edit, and manage bus information
- **Route Management**: Create and manage bus routes and stops
- **Real-time Monitoring**: Monitor bus locations and system health

### Technical Features
- **REST API**: Complete API for location updates and data retrieval
- **Simulated GPS Data**: Realistic bus simulator for testing and demonstration
- **Session-based User Tracking**: Anonymous user location tracking
- **Distance Calculation**: Haversine formula for accurate distance calculations
- **Scalable Architecture**: Easy transition from simulator to real GPS hardware

## 🏗️ Architecture

```
bus_tracking_project/
├── tracking_app/           # Main Django app
│   ├── models.py          # Database models (Bus, Route, BusLocation, etc.)
│   ├── views.py           # API endpoints and web views
│   ├── admin.py           # Django admin configuration
│   ├── urls.py            # URL routing
│   └── management/        # Management commands
├── mytrackingproject/     # Django project settings
├── bus_simulator.py       # Enhanced GPS simulator
├── index.html            # Main tracking interface
├── admin_dashboard.html   # Admin management interface
└── db.sqlite3            # SQLite database
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd bus_tracking_project
   ```

2. **Activate virtual environment** (if exists)
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies** (if not already installed)
   ```bash
   pip install django requests
   ```

4. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Set up demo data**
   ```bash
   python manage.py setup_demo_data
   ```

6. **Start the Django server**
   ```bash
   python manage.py runserver
   ```

7. **Run the bus simulator** (in a new terminal)
   ```bash
   python bus_simulator.py
   ```

8. **Access the application**
   - Main Interface: http://localhost:8000/
   - Admin Dashboard: http://localhost:8000/admin_panel/
   - Django Admin: http://localhost:8000/admin/ (admin/admin123)

## 📱 Usage

### Main Tracking Interface

1. **View Real-time Buses**: The map shows all active buses with their current locations
2. **Use Your Location**: Click "Use My Location" to enable GPS-based features
3. **Find Nearest Buses**: Set a radius and click "Find Nearest Buses"
4. **Search Buses**: Use the search box to find specific buses or routes
5. **Refresh Data**: Click "Refresh Now" to update bus locations immediately

### Admin Dashboard

1. **View Statistics**: See total buses, active buses, and routes
2. **Add New Buses**: Fill in the form to add buses to specific routes
3. **Manage Existing Buses**: View, search, and manage all buses
4. **Export Data**: Download bus data as CSV for external use

## 🔧 API Endpoints

### Bus Location APIs
- `POST /api/update_location/` - Update bus location (for GPS devices)
- `GET /api/get_locations/` - Get all active bus locations

### User Location & Nearest Bus APIs
- `POST /api/update_user_location/` - Update user's location
- `GET /api/find_nearest_buses/?lat={lat}&lng={lng}&radius={km}` - Find nearest buses

### Search & Route APIs
- `GET /api/search_buses/?q={query}` - Search buses
- `GET /api/routes/` - Get all routes

### Admin APIs
- `POST /api/admin/add_bus/` - Add new bus (admin)
- `GET /api/admin/list_buses/` - List all buses (admin)

## 🛠️ Configuration

### Settings Configuration
The system is configured in `mytrackingproject/settings.py`:
- Database: SQLite (easily changeable to PostgreSQL/MySQL)
- Debug mode: Enabled for development
- CORS: Configured for local development
- Sessions: 24-hour session timeout

### Bus Simulator Configuration
Edit `bus_simulator.py` to modify:
- Bus routes and coordinates
- Speed ranges for different bus types
- Update intervals and GPS variation
- Number of simulated buses

## 🎯 Transitioning to Real GPS Data

The system is designed for easy transition from simulated to real GPS data:

### For Real GPS Integration:

1. **Hardware Setup**: Install GPS devices in buses
2. **Replace Simulator**: Replace `bus_simulator.py` with real GPS data collection
3. **Update Endpoints**: The API endpoints remain the same
4. **Authentication**: Add API key authentication for production
5. **Database**: Switch to PostgreSQL for production use

### Example Real GPS Integration:
```python
# Real GPS device code example
import requests
import json
import gps

def send_real_location(bus_id, gps_data):
    url = "http://your-server.com/api/update_location/"
    data = {
        'bus_id': bus_id,
        'latitude': gps_data.latitude,
        'longitude': gps_data.longitude,
        'speed': gps_data.speed,
        'heading': gps_data.track
    }
    response = requests.post(url, json=data)
    return response.status_code == 200
```

## 📊 Database Models

### Route
- `route_id`: Unique route identifier
- `name`: Human-readable route name
- `start_location`, `end_location`: Route endpoints
- `description`: Route description
- `is_active`: Whether route is currently active

### Bus
- `bus_id`: Unique bus identifier
- `bus_number`: Vehicle registration number
- `route`: Foreign key to Route
- `driver_name`: Driver's name
- `capacity`: Passenger capacity
- `is_active`: Whether bus is currently active

### BusLocation
- `bus`: Foreign key to Bus
- `latitude`, `longitude`: GPS coordinates
- `speed`: Current speed in km/h
- `heading`: Direction in degrees
- `last_updated`: Timestamp of location update

### UserLocation
- `user`: Foreign key to User (optional)
- `session_id`: Session identifier for anonymous users
- `latitude`, `longitude`: User's GPS coordinates
- `accuracy`: GPS accuracy in meters

### BusStop
- `stop_id`: Unique stop identifier
- `name`: Stop name
- `latitude`, `longitude`: Stop coordinates
- `routes`: Many-to-many relationship with Routes

## 🔒 Security Considerations

### Current Development Setup:
- CSRF protection disabled for API endpoints
- All origins allowed for CORS
- Simple session-based tracking

### Production Recommendations:
- Enable CSRF protection with proper token handling
- Restrict CORS to specific domains
- Add API key authentication
- Use HTTPS for all communications
- Implement rate limiting
- Add input validation and sanitization

## 🧪 Testing

### Manual Testing:
1. Start the server and simulator
2. Open multiple browser tabs to test concurrent users
3. Test geolocation features in different browsers
4. Verify API responses using browser developer tools

### Adding Automated Tests:
```bash
# Create test file: tracking_app/tests.py
python manage.py test
```

## 📈 Performance Optimization

### For Production:
1. **Database Optimization**: 
   - Add database indexes
   - Use connection pooling
   - Consider caching frequent queries

2. **API Optimization**:
   - Implement API rate limiting
   - Add response caching
   - Use CDN for static assets

3. **Real-time Updates**:
   - Consider WebSocket connections
   - Implement server-sent events
   - Add push notifications

## 🤝 Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is created for educational and demonstration purposes. Feel free to use and modify as needed.

## 🆘 Troubleshooting

### Common Issues:

**Simulator not connecting to server:**
- Ensure Django server is running on port 8000
- Check firewall settings
- Verify API endpoints are accessible

**Geolocation not working:**
- Use HTTPS in production (HTTP only works on localhost)
- Check browser permissions for location access
- Ensure user grants location permission

**Database errors:**
- Run migrations: `python manage.py migrate`
- Clear existing data: `python manage.py setup_demo_data --clear`
- Check database file permissions

**Map not displaying:**
- Google Maps requires API key for production
- Simple canvas map should work without API key
- Check browser console for JavaScript errors

## 📞 Support

For questions or issues, please:
1. Check this README for solutions
2. Review the Django documentation
3. Check browser developer tools for errors
4. Verify all services are running correctly

---

**Happy Tracking! 🚌📍**
>>>>>>> b6e5fa6 (basic)
