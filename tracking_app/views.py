from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import json
import uuid
from .models import BusLocation, Bus, Route, UserLocation, BusStop

# Create your views here.

# ============= Bus Location APIs =============

@csrf_exempt
@require_http_methods(["POST"])
def update_location(request):
    """API endpoint for buses to send their location updates"""
    try:
        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        speed = data.get('speed', 0.0)
        heading = data.get('heading', 0.0)
        
        if not bus_id or latitude is None or longitude is None:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Ensure a default route exists for simulated data
        default_route, _ = Route.objects.get_or_create(
            route_id='ROUTE-DEFAULT',
            defaults={
                'name': 'Default Simulation Route',
                'start_location': 'Start',
                'end_location': 'End',
                'description': 'Autocreated route for simulator data'
            }
        )

        # Get or create bus object
        bus, bus_created = Bus.objects.get_or_create(
            bus_id=bus_id,
            defaults={
                'bus_number': bus_id,
                'route': default_route
            }
        )
        
        # Create new location record (keeping history)
        bus_location = BusLocation.objects.create(
            bus=bus,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            heading=heading
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Location updated successfully',
            'bus_created': bus_created,
            'location_id': bus_location.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_locations(request):
    """Get current locations of all active buses"""
    try:
        # Get the latest location for each bus
        latest_locations = []
        buses = Bus.objects.filter(is_active=True).prefetch_related('locations')
        
        for bus in buses:
            latest_location = bus.locations.first()  # Latest due to ordering
            if latest_location:
                latest_locations.append({
                    'bus_id': bus.bus_id,
                    'bus_number': bus.bus_number,
                    'route_id': bus.route.route_id if bus.route else None,
                    'route_name': bus.route.name if bus.route else None,
                    'latitude': latest_location.latitude,
                    'longitude': latest_location.longitude,
                    'speed': latest_location.speed,
                    'heading': latest_location.heading,
                    'last_updated': latest_location.last_updated.isoformat(),
                    'driver_name': bus.driver_name
                })
        
        return JsonResponse({
            'status': 'success',
            'locations': latest_locations,
            'count': len(latest_locations)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= User Location & Nearest Bus APIs =============

@csrf_exempt
@require_http_methods(["POST"])
def update_user_location(request):
    """Update user's current location"""
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy', 0.0)
        
        if latitude is None or longitude is None:
            return JsonResponse({'error': 'Missing latitude or longitude'}, status=400)
        
        # Use session ID for anonymous users
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        user = request.user if request.user.is_authenticated else None
        
        # Update or create user location
        user_location, created = UserLocation.objects.update_or_create(
            user=user,
            session_id=session_id if not user else '',
            defaults={
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': accuracy
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'User location updated successfully',
            'location_id': user_location.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def find_nearest_buses(request):
    """Find nearest buses to user's location"""
    try:
        # Get user's location parameters
        latitude = request.GET.get('lat')
        longitude = request.GET.get('lng')
        radius = float(request.GET.get('radius', 5.0))  # Default 5km radius
        limit = int(request.GET.get('limit', 10))  # Default 10 buses
        
        if not latitude or not longitude:
            return JsonResponse({'error': 'Missing latitude or longitude'}, status=400)
        
        latitude = float(latitude)
        longitude = float(longitude)
        
        # Create temporary user location object
        temp_user_location = UserLocation(
            latitude=latitude,
            longitude=longitude
        )
        
        # Find nearest buses
        nearest_buses = temp_user_location.find_nearest_buses(radius, limit)
        
        # Format response
        buses_data = []
        for bus_info in nearest_buses:
            bus = bus_info['bus']
            location = bus_info['location']
            buses_data.append({
                'bus_id': bus.bus_id,
                'bus_number': bus.bus_number,
                'route_id': bus.route.route_id if bus.route else None,
                'route_name': bus.route.name if bus.route else None,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'distance_km': bus_info['distance'],
                'speed': location.speed,
                'last_updated': location.last_updated.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'nearest_buses': buses_data,
            'count': len(buses_data),
            'search_radius_km': radius,
            'user_location': {
                'latitude': latitude,
                'longitude': longitude
            }
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Invalid parameter: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= Bus Search APIs =============

@require_http_methods(["GET"])
def search_buses(request):
    """Search buses by various criteria"""
    try:
        query = request.GET.get('q', '').strip()
        route_id = request.GET.get('route')
        
        buses = Bus.objects.filter(is_active=True).select_related('route')
        
        if query:
            buses = buses.filter(
                Q(bus_id__icontains=query) |
                Q(bus_number__icontains=query) |
                Q(route__name__icontains=query) |
                Q(route__route_id__icontains=query)
            )
        
        if route_id:
            buses = buses.filter(route__route_id=route_id)
        
        # Get current locations for found buses
        buses_data = []
        for bus in buses:
            current_location = bus.get_current_location()
            buses_data.append({
                'bus_id': bus.bus_id,
                'bus_number': bus.bus_number,
                'route_id': bus.route.route_id if bus.route else None,
                'route_name': bus.route.name if bus.route else None,
                'driver_name': bus.driver_name,
                'capacity': bus.capacity,
                'current_location': {
                    'latitude': current_location.latitude,
                    'longitude': current_location.longitude,
                    'speed': current_location.speed,
                    'last_updated': current_location.last_updated.isoformat()
                } if current_location else None
            })
        
        return JsonResponse({
            'status': 'success',
            'buses': buses_data,
            'count': len(buses_data),
            'query': query
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_routes(request):
    """Get all available routes"""
    try:
        routes = Route.objects.filter(is_active=True).prefetch_related('buses')
        
        routes_data = []
        for route in routes:
            active_buses = route.buses.filter(is_active=True).count()
            routes_data.append({
                'route_id': route.route_id,
                'name': route.name,
                'start_location': route.start_location,
                'end_location': route.end_location,
                'description': route.description,
                'active_buses': active_buses,
                'created_at': route.created_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'routes': routes_data,
            'count': len(routes_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= Admin APIs =============

@csrf_exempt
@require_http_methods(["POST"])
def admin_add_bus(request):
    """Admin endpoint to add a new bus"""
    try:
        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        bus_number = data.get('bus_number')
        route_id = data.get('route_id')
        driver_name = data.get('driver_name', '')
        capacity = data.get('capacity', 50)
        
        if not bus_id or not bus_number or not route_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Check if route exists
        try:
            route = Route.objects.get(route_id=route_id)
        except Route.DoesNotExist:
            return JsonResponse({'error': 'Route not found'}, status=404)
        
        # Create bus
        bus, created = Bus.objects.get_or_create(
            bus_id=bus_id,
            defaults={
                'bus_number': bus_number,
                'route': route,
                'driver_name': driver_name,
                'capacity': capacity
            }
        )
        
        if not created:
            return JsonResponse({'error': 'Bus with this ID already exists'}, status=400)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Bus added successfully',
            'bus': {
                'bus_id': bus.bus_id,
                'bus_number': bus.bus_number,
                'route_id': bus.route.route_id,
                'driver_name': bus.driver_name,
                'capacity': bus.capacity
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_list_buses(request):
    """Admin endpoint to list all buses"""
    try:
        buses = Bus.objects.all().select_related('route')
        
        buses_data = []
        for bus in buses:
            current_location = bus.get_current_location()
            buses_data.append({
                'id': bus.id,
                'bus_id': bus.bus_id,
                'bus_number': bus.bus_number,
                'route_id': bus.route.route_id if bus.route else None,
                'route_name': bus.route.name if bus.route else None,
                'driver_name': bus.driver_name,
                'capacity': bus.capacity,
                'is_active': bus.is_active,
                'created_at': bus.created_at.isoformat(),
                'current_location': {
                    'latitude': current_location.latitude,
                    'longitude': current_location.longitude,
                    'last_updated': current_location.last_updated.isoformat()
                } if current_location else None
            })
        
        return JsonResponse({
            'status': 'success',
            'buses': buses_data,
            'count': len(buses_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= Authentication Views =============

@csrf_exempt  
@require_http_methods(["POST"])
def admin_authenticate(request):
    """Simple admin authentication endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        user = authenticate(username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': 'Authentication successful',
                'redirect_url': '/admin_panel/'
            })
        else:
            return JsonResponse({'error': 'Invalid credentials or insufficient permissions'}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def admin_logout_view(request):
    """Admin logout endpoint"""
    logout(request)
    return JsonResponse({'status': 'success', 'message': 'Logged out successfully'})

# ============= Web Views =============

def home(request):
    """Main dashboard view"""
    return render(request, 'tracking_app/index.html')

@login_required
def admin_dashboard(request):
    """Admin dashboard view - requires authentication"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
    return render(request, 'tracking_app/admin_dashboard.html')
