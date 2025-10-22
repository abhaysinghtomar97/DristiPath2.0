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
from math import cos, radians
from .models import BusLocation, Bus, Route, UserLocation, BusStop, Driver, Schedule, ScheduleException
from .location_utils import get_location_name, get_route_display_name, invalidate_user_cache

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
                # Get human-readable location name
                location_name = get_location_name(latest_location.latitude, latest_location.longitude)
                route_display_name = get_route_display_name(bus.route)
                
                latest_locations.append({
                    'bus_id': bus.bus_id,
                    'bus_number': bus.bus_number,
                    'route_id': bus.route.route_id if bus.route else None,
                    'route_name': bus.route.name if bus.route else None,
                    'route_display_name': route_display_name,
                    'latitude': latest_location.latitude,
                    'longitude': latest_location.longitude,
                    'location_name': location_name,  # Human-readable location
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
    """Find nearest buses to user's location - SIMPLE AND FAST"""
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
        
        # SIMPLE APPROACH: Get all active bus locations with select_related to avoid N+1 queries
        bus_locations = BusLocation.objects.select_related(
            'bus', 'bus__route'
        ).filter(
            bus__is_active=True
        ).order_by('-last_updated')  # Get latest locations first
        
        # Calculate distances and find nearby buses
        nearby_buses = []
        for bus_location in bus_locations:
            distance = BusLocation.calculate_distance(
                latitude, longitude,
                bus_location.latitude, bus_location.longitude
            )
            
            if distance <= radius:
                # Use cached/predefined location names to avoid slow API calls
                location_name = get_location_name(bus_location.latitude, bus_location.longitude)
                route_display_name = get_route_display_name(bus_location.bus.route)
                
                nearby_buses.append({
                    'bus_id': bus_location.bus.bus_id,
                    'bus_number': bus_location.bus.bus_number,
                    'route_id': bus_location.bus.route.route_id if bus_location.bus.route else None,
                    'route_name': bus_location.bus.route.name if bus_location.bus.route else None,
                    'route_display_name': route_display_name,
                    'latitude': bus_location.latitude,
                    'longitude': bus_location.longitude,
                    'location_name': location_name,
                    'distance_km': round(distance, 2),
                    'speed': bus_location.speed,
                    'current_speed': bus_location.bus.current_speed,
                    'driver_name': bus_location.bus.driver_name,
                    'driver_mobile': bus_location.bus.driver_mobile,
                    'last_updated': bus_location.last_updated.isoformat()
                })
        
        # Sort by distance and limit results
        nearby_buses.sort(key=lambda x: x['distance_km'])
        nearby_buses = nearby_buses[:limit]
        
        return JsonResponse({
            'status': 'success',
            'nearest_buses': nearby_buses,
            'count': len(nearby_buses),
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
    """Search vehicles by various criteria"""
    try:
        query = request.GET.get('q', '').strip()
        route_id = request.GET.get('route')
        vtype = (request.GET.get('type') or '').strip().lower()
        
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
        if vtype:
            buses = buses.filter(vehicle_type=vtype)
        
        # Get current locations for found vehicles
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
                'vehicle_type': bus.vehicle_type,
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
            'query': query,
            'type': vtype,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_routes(request):
    """Get all available routes (public aggregator across owners)"""
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
    """Admin endpoint to add a new vehicle owned by the current admin"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)

        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        bus_number = data.get('bus_number')
        route_id = data.get('route_id')
        driver_name = data.get('driver_name', '')
        capacity = data.get('capacity', 50)
        vehicle_type = (data.get('vehicle_type') or 'bus').lower()

        valid_types = {choice[0] for choice in Bus.VEHICLE_TYPES}
        if vehicle_type not in valid_types:
            return JsonResponse({'error': f'Invalid vehicle_type. Allowed: {sorted(list(valid_types))}'}, status=400)
        if not bus_id or not bus_number or not route_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Route must belong to this admin
        try:
            route = Route.objects.get(route_id=route_id, owner=request.user)
        except Route.DoesNotExist:
            return JsonResponse({'error': 'Route not found for this admin'}, status=404)

        # Create vehicle scoped to owner
        bus, created = Bus.objects.get_or_create(
            owner=request.user,
            bus_id=bus_id,
            defaults={
                'bus_number': bus_number,
                'route': route,
                'driver_name': driver_name,
                'capacity': capacity,
                'vehicle_type': vehicle_type,
                'is_active': True,
            }
        )
        if not created:
            return JsonResponse({'error': 'Vehicle with this ID already exists for this admin'}, status=400)

        return JsonResponse({
            'status': 'success',
            'message': 'Vehicle added successfully',
            'vehicle': {
                'bus_id': bus.bus_id,
                'bus_number': bus.bus_number,
                'route_id': bus.route.route_id,
                'driver_name': bus.driver_name,
                'capacity': bus.capacity,
                'vehicle_type': bus.vehicle_type,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_list_buses(request):
    """Admin endpoint to list all vehicles owned by current admin"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)

        buses = Bus.objects.filter(owner=request.user).select_related('route')
        
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
                'vehicle_type': bus.vehicle_type,
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
@require_http_methods(["POST"])
def admin_signup(request):
    """Create a new admin (staff) user. For development use. In production, restrict this."""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        full_name = data.get('full_name', '').strip()
        admin_code = data.get('admin_code', '')  # optional code for gating
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        # Basic password policy
        if len(password) < 6:
            return JsonResponse({'error': 'Password must be at least 6 characters long'}, status=400)
        
        # Optional: gate behind a simple code if provided by client
        from django.conf import settings
        expected_code = getattr(settings, 'ADMIN_SIGNUP_CODE', '')
        if expected_code:
            if admin_code != expected_code:
                return JsonResponse({'error': 'Invalid admin access code'}, status=403)
        
        # Ensure username unique
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create_user(username=username, email=email or None, password=password)
        if full_name:
            # Split full name into first/last if possible
            parts = full_name.split()
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = ' '.join(parts[1:])
        user.is_staff = True
        user.save()
        
        login(request, user)
        return JsonResponse({'status': 'success', 'message': 'Admin account created', 'redirect_url': '/admin_panel/'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def admin_logout_view(request):
    """Admin logout endpoint"""
    logout(request)
    return JsonResponse({'status': 'success', 'message': 'Logged out successfully'})

# ============= User Authentication Views =============

@require_http_methods(["GET"])
def get_csrf_token(request):
    """Get CSRF token for authentication forms"""
    from django.middleware.csrf import get_token
    return JsonResponse({
        'csrf_token': get_token(request)
    })

@csrf_exempt  
@require_http_methods(["POST"])
def user_authenticate(request):
    """User authentication endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': 'Authentication successful',
                'redirect_url': '/user/',
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def user_signup(request):
    """Create a new regular user account"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        full_name = data.get('full_name', '').strip()
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        # Basic password policy
        if len(password) < 6:
            return JsonResponse({'error': 'Password must be at least 6 characters long'}, status=400)
        
        # Ensure username unique
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        # Validate email if provided
        if email and User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        # Create regular user (not staff)
        user = User.objects.create_user(username=username, email=email or None, password=password)
        if full_name:
            # Split full name into first/last if possible
            parts = full_name.split()
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = ' '.join(parts[1:])
            user.save()
        
        # Automatically login the user after signup
        login(request, user)
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Account created successfully', 
            'redirect_url': '/user/',
            'user': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def user_logout_view(request):
    """User logout endpoint"""
    logout(request)
    return JsonResponse({'status': 'success', 'message': 'Logged out successfully'})

# ============= Admin Management Endpoints =============

@csrf_exempt
@require_http_methods(["POST"])
def admin_toggle_bus_status(request):
    """Toggle vehicle (bus) active status for this admin's vehicle."""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        is_active = data.get('is_active')
        if bus_id is None or is_active is None:
            return JsonResponse({'error': 'bus_id and is_active are required'}, status=400)
        try:
            bus = Bus.objects.get(owner=request.user, bus_id=bus_id)
        except Bus.DoesNotExist:
            return JsonResponse({'error': 'Vehicle not found for this admin'}, status=404)
        bus.is_active = bool(is_active)
        bus.save(update_fields=['is_active'])
        return JsonResponse({'status': 'success', 'bus_id': bus.bus_id, 'is_active': bus.is_active})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_update_bus_route(request):
    """Dynamically change bus route assignment without interrupting service."""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        new_route_id = data.get('route_id')
        
        if not bus_id or not new_route_id:
            return JsonResponse({'error': 'bus_id and route_id are required'}, status=400)
        
        # Get the bus
        try:
            bus = Bus.objects.get(owner=request.user, bus_id=bus_id)
        except Bus.DoesNotExist:
            return JsonResponse({'error': 'Vehicle not found for this admin'}, status=404)
        
        # Get the new route
        try:
            new_route = Route.objects.get(owner=request.user, route_id=new_route_id)
        except Route.DoesNotExist:
            return JsonResponse({'error': 'Route not found for this admin'}, status=404)
        
        # Store old route for response
        old_route_id = bus.route.route_id if bus.route else None
        
        # Update bus route
        bus.route = new_route
        bus.save(update_fields=['route'])
        
        return JsonResponse({
            'status': 'success',
            'message': 'Bus route updated successfully',
            'bus_id': bus.bus_id,
            'old_route_id': old_route_id,
            'new_route_id': new_route.route_id,
            'new_route_name': new_route.name
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_update_bus_driver(request):
    """Dynamically change bus driver assignment."""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        driver_name = data.get('driver_name', '')
        driver_mobile = data.get('driver_mobile', '')
        
        if not bus_id:
            return JsonResponse({'error': 'bus_id is required'}, status=400)
        
        # Get the bus
        try:
            bus = Bus.objects.get(owner=request.user, bus_id=bus_id)
        except Bus.DoesNotExist:
            return JsonResponse({'error': 'Vehicle not found for this admin'}, status=404)
        
        # Store old driver info for response
        old_driver_name = bus.driver_name
        old_driver_mobile = bus.driver_mobile
        
        # Update bus driver info
        bus.driver_name = driver_name
        bus.driver_mobile = driver_mobile
        bus.save(update_fields=['driver_name', 'driver_mobile'])
        
        return JsonResponse({
            'status': 'success',
            'message': 'Bus driver updated successfully',
            'bus_id': bus.bus_id,
            'old_driver': {
                'name': old_driver_name,
                'mobile': old_driver_mobile
            },
            'new_driver': {
                'name': driver_name,
                'mobile': driver_mobile
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_update_bus_comprehensive(request):
    """Comprehensive bus update: status, route, and driver in one atomic operation."""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        
        if not bus_id:
            return JsonResponse({'error': 'bus_id is required'}, status=400)
        
        # Get the bus
        try:
            bus = Bus.objects.get(owner=request.user, bus_id=bus_id)
        except Bus.DoesNotExist:
            return JsonResponse({'error': 'Vehicle not found for this admin'}, status=404)
        
        # Store old values for response
        old_values = {
            'is_active': bus.is_active,
            'route_id': bus.route.route_id if bus.route else None,
            'driver_name': bus.driver_name,
            'driver_mobile': bus.driver_mobile
        }
        
        updates = []
        new_values = {}
        
        # Handle status change
        if 'is_active' in data:
            bus.is_active = bool(data['is_active'])
            updates.append('is_active')
            new_values['is_active'] = bus.is_active
        
        # Handle route change
        if 'route_id' in data:
            try:
                new_route = Route.objects.get(owner=request.user, route_id=data['route_id'])
                bus.route = new_route
                updates.append('route')
                new_values['route_id'] = new_route.route_id
                new_values['route_name'] = new_route.name
            except Route.DoesNotExist:
                return JsonResponse({'error': 'Route not found for this admin'}, status=404)
        
        # Handle driver changes
        if 'driver_name' in data:
            bus.driver_name = data.get('driver_name', '')
            updates.append('driver_name')
            new_values['driver_name'] = bus.driver_name
        
        if 'driver_mobile' in data:
            bus.driver_mobile = data.get('driver_mobile', '')
            updates.append('driver_mobile')
            new_values['driver_mobile'] = bus.driver_mobile
        
        # Save changes atomically
        if updates:
            bus.save(update_fields=updates)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Bus updated successfully ({len(updates)} fields changed)',
            'bus_id': bus.bus_id,
            'updated_fields': updates,
            'old_values': old_values,
            'new_values': new_values
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_add_route(request):
    """Create a new route owned by the current admin."""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        data = json.loads(request.body)
        route_id = data.get('route_id')
        name = data.get('name')
        start_location = data.get('start_location')
        end_location = data.get('end_location')
        description = data.get('description', '')
        if not route_id or not name or not start_location or not end_location:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        route, created = Route.objects.get_or_create(
            owner=request.user,
            route_id=route_id,
            defaults={
                'name': name,
                'start_location': start_location,
                'end_location': end_location,
                'description': description
            }
        )
        if not created:
            return JsonResponse({'error': 'Route with this ID already exists for this admin'}, status=400)
        return JsonResponse({'status': 'success', 'route': {
            'route_id': route.route_id,
            'name': route.name,
            'start_location': route.start_location,
            'end_location': route.end_location,
            'description': route.description,
        }})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_clean_old_locations(request):
    """Delete BusLocation rows from the last 24 hours for current admin's vehicles."""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)

        cutoff = timezone.now() - timedelta(hours=2)  # last 24 hours
        deleted, _ = BusLocation.objects.filter(bus__owner=request.user, last_updated__gte=cutoff).delete()

        return JsonResponse({'status': 'success', 'deleted': deleted, 'message': 'Deleted data from last 24 hours'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= Admin Routes List =============

@require_http_methods(["GET"])
def admin_list_routes(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
    try:
        routes = Route.objects.filter(owner=request.user, is_active=True)
        data = [{
            'route_id': r.route_id,
            'name': r.name,
            'start_location': r.start_location,
            'end_location': r.end_location,
            'description': r.description,
            'created_at': r.created_at.isoformat(),
        } for r in routes]
        return JsonResponse({'status': 'success', 'routes': data, 'count': len(data)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= Admin Analytics =============

@require_http_methods(["GET"])
@login_required
def admin_analytics(request):
    """Return analytics data for admin dashboard, scoped to current admin.
    Includes vehicle type distribution for per-admin isolated charts.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
    try:
        from django.db.models import Count
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        five_min_ago = now - timedelta(minutes=5)
        three_min_ago = now - timedelta(minutes=3)
        
        total_buses = Bus.objects.filter(owner=request.user).count()
        active_buses = Bus.objects.filter(owner=request.user, is_active=True).count()
        total_routes = Route.objects.filter(owner=request.user).count()
        total_locations = BusLocation.objects.filter(bus__owner=request.user).count()
        loc_last_hour = BusLocation.objects.filter(bus__owner=request.user, last_updated__gte=one_hour_ago).count()
        loc_last_day = BusLocation.objects.filter(bus__owner=request.user, last_updated__gte=one_day_ago).count()
        
        # FIXED: Active vehicles count based on last_seen in last 5 minutes
        recent_bus_ids = BusLocation.objects.filter(
            bus__owner=request.user, 
            last_updated__gte=five_min_ago
        ).values_list('bus__id', flat=True).distinct()
        active_recent = Bus.objects.filter(owner=request.user, id__in=recent_bus_ids, is_active=True).count()
        
        # Vehicle type distribution (per-admin)
        type_counts_qs = (
            Bus.objects.filter(owner=request.user)
            .values('vehicle_type')
            .annotate(count=Count('id'))
        )
        # Ensure all types appear with zeros if missing
        allowed_types = [t for t, _ in Bus.VEHICLE_TYPES]
        vehicle_type_counts = {t: 0 for t in allowed_types}
        for row in type_counts_qs:
            vehicle_type_counts[row['vehicle_type']] = row['count']
        status_counts = {
            'active': active_buses,
            'inactive': total_buses - active_buses,
        }
        
        # Per-route stats
        route_stats = []
        for route in Route.objects.filter(owner=request.user):
            buses_qs = route.buses.all()
            bus_ids = list(buses_qs.values_list('id', flat=True))
            recent_count = (
                BusLocation.objects
                .filter(bus_id__in=bus_ids, last_updated__gte=three_min_ago)
                .values('bus_id').distinct().count()
            )
            route_stats.append({
                'route_id': route.route_id,
                'name': route.name,
                'buses': buses_qs.count(),
                'active_recent': recent_count,
            })
        
        # Recent activity entries
        recent_locations = (
            BusLocation.objects.select_related('bus')
            .filter(bus__owner=request.user)
            .order_by('-last_updated')[:20]
        )
        recent_activity = [{
            'bus_id': bl.bus.bus_id,
            'bus_number': bl.bus.bus_number,
            'route_id': bl.bus.route.route_id if bl.bus.route else None,
            'latitude': bl.latitude,
            'longitude': bl.longitude,
            'speed': bl.speed,
            'heading': bl.heading,
            'last_updated': bl.last_updated.isoformat(),
        } for bl in recent_locations]
        
        data = {
            'status': 'success',
            'summary': {
                'total_buses': total_buses,
                'active_buses': active_buses,
                'total_routes': total_routes,
                'total_locations': total_locations,
                'updates_last_hour': loc_last_hour,
                'updates_last_24h': loc_last_day,
                'active_recent': active_recent,
            },
            'vehicle_type_counts': vehicle_type_counts,
            'status_counts': status_counts,
            'routes': route_stats,
            'recent_activity': recent_activity,
            'generated_at': now.isoformat(),
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= Web Views =============

def home(request):
    """Main dashboard view"""
    return render(request, 'tracking_app/index.html')

@login_required
def admin_dashboard(request):
    """Admin dashboard view - requires authentication"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
    # Render template
    return render(request, 'admin_dashboard.html')

def serve_debug_test(request):
    return render(request, 'debug_test.html')

# ============= Dynamic Scheduling APIs =============

@csrf_exempt
@require_http_methods(["POST"])
def admin_add_driver(request):
    """Add a new driver"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        data = json.loads(request.body)
        driver_id = data.get('driver_id')
        name = data.get('name')
        mobile = data.get('mobile', '')
        license_number = data.get('license_number', '')
        email = data.get('email', '')
        
        if not driver_id or not name:
            return JsonResponse({'error': 'Driver ID and name are required'}, status=400)
        
        # Create driver scoped to owner
        driver, created = Driver.objects.get_or_create(
            owner=request.user,
            driver_id=driver_id,
            defaults={
                'name': name,
                'mobile': mobile,
                'license_number': license_number,
                'email': email,
                'is_active': True,
            }
        )
        
        if not created:
            return JsonResponse({'error': 'Driver with this ID already exists'}, status=400)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Driver added successfully',
            'driver': {
                'driver_id': driver.driver_id,
                'name': driver.name,
                'mobile': driver.mobile,
                'license_number': driver.license_number,
                'email': driver.email,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_list_drivers(request):
    """List all drivers owned by current admin"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        drivers = Driver.objects.filter(owner=request.user, is_active=True)
        
        drivers_data = [{
            'id': driver.id,
            'driver_id': driver.driver_id,
            'name': driver.name,
            'mobile': driver.mobile,
            'license_number': driver.license_number,
            'email': driver.email,
            'is_active': driver.is_active,
            'created_at': driver.created_at.isoformat(),
        } for driver in drivers]
        
        return JsonResponse({
            'status': 'success',
            'drivers': drivers_data,
            'count': len(drivers_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_add_schedule(request):
    """Create a new dynamic schedule"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        name = data.get('name')
        bus_id = data.get('bus_id')
        route_id = data.get('route_id')
        driver_id = data.get('driver_id')  # Optional
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        days_of_week = data.get('days_of_week', [])
        effective_from = data.get('effective_from')
        effective_to = data.get('effective_to')  # Optional
        priority = data.get('priority', 1)
        
        # Validate required fields
        if not all([schedule_id, name, bus_id, route_id, start_time, end_time, effective_from]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Validate bus belongs to admin
        try:
            bus = Bus.objects.get(owner=request.user, bus_id=bus_id)
        except Bus.DoesNotExist:
            return JsonResponse({'error': 'Bus not found for this admin'}, status=404)
        
        # Validate route belongs to admin
        try:
            route = Route.objects.get(owner=request.user, route_id=route_id)
        except Route.DoesNotExist:
            return JsonResponse({'error': 'Route not found for this admin'}, status=404)
        
        # Validate driver if provided
        driver = None
        if driver_id:
            try:
                driver = Driver.objects.get(owner=request.user, driver_id=driver_id)
            except Driver.DoesNotExist:
                return JsonResponse({'error': 'Driver not found for this admin'}, status=404)
        
        # Parse dates and times
        from datetime import datetime, time, date
        try:
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            effective_from_date = datetime.strptime(effective_from, '%Y-%m-%d').date()
            effective_to_date = None
            if effective_to:
                effective_to_date = datetime.strptime(effective_to, '%Y-%m-%d').date()
        except ValueError as e:
            return JsonResponse({'error': f'Invalid date/time format: {str(e)}'}, status=400)
        
        # Check for schedule conflicts before creating
        conflict_error = check_schedule_conflicts(
            request.user, bus, driver, start_time_obj, end_time_obj, 
            days_of_week, effective_from_date, effective_to_date
        )
        
        if conflict_error:
            return JsonResponse({'error': conflict_error}, status=400)
        
        # Create schedule
        schedule, created = Schedule.objects.get_or_create(
            owner=request.user,
            schedule_id=schedule_id,
            defaults={
                'name': name,
                'bus': bus,
                'route': route,
                'driver': driver,
                'start_time': start_time_obj,
                'end_time': end_time_obj,
                'days_of_week': days_of_week,
                'effective_from': effective_from_date,
                'effective_to': effective_to_date,
                'priority': priority,
                'is_active': True,
            }
        )
        
        if not created:
            return JsonResponse({'error': 'Schedule with this ID already exists'}, status=400)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Schedule created successfully',
            'schedule': {
                'schedule_id': schedule.schedule_id,
                'name': schedule.name,
                'bus_id': schedule.bus.bus_id,
                'route_id': schedule.route.route_id,
                'driver_id': schedule.driver.driver_id if schedule.driver else None,
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'days_of_week': schedule.days_of_week,
                'effective_from': schedule.effective_from.isoformat(),
                'effective_to': schedule.effective_to.isoformat() if schedule.effective_to else None,
                'priority': schedule.priority,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_list_schedules(request):
    """List all schedules owned by current admin"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        schedules = Schedule.objects.filter(
            owner=request.user
        ).select_related('bus', 'route', 'driver')
        
        schedules_data = []
        for schedule in schedules:
            schedules_data.append({
                'id': schedule.id,
                'schedule_id': schedule.schedule_id,
                'name': schedule.name,
                'bus': {
                    'bus_id': schedule.bus.bus_id,
                    'bus_number': schedule.bus.bus_number,
                    'vehicle_type': schedule.bus.vehicle_type,
                },
                'route': {
                    'route_id': schedule.route.route_id,
                    'name': schedule.route.name,
                    'start_location': schedule.route.start_location,
                    'end_location': schedule.route.end_location,
                },
                'driver': {
                    'driver_id': schedule.driver.driver_id,
                    'name': schedule.driver.name,
                    'mobile': schedule.driver.mobile,
                } if schedule.driver else None,
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'days_of_week': schedule.days_of_week,
                'weekdays_display': schedule.get_weekdays_display(),
                'effective_from': schedule.effective_from.isoformat(),
                'effective_to': schedule.effective_to.isoformat() if schedule.effective_to else None,
                'priority': schedule.priority,
                'is_active': schedule.is_active,
                'is_active_now': schedule.is_active_now(),
                'created_at': schedule.created_at.isoformat(),
                'updated_at': schedule.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'status': 'success',
            'schedules': schedules_data,
            'count': len(schedules_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def admin_add_schedule_exception(request):
    """Add a schedule exception"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        data = json.loads(request.body)
        bus_id = data.get('bus_id')
        exception_date = data.get('exception_date')
        exception_type = data.get('exception_type')
        reason = data.get('reason', '')
        
        # Optional override values
        override_route_id = data.get('override_route_id')
        override_driver_id = data.get('override_driver_id')
        override_start_time = data.get('override_start_time')
        override_end_time = data.get('override_end_time')
        
        # Validate required fields
        if not all([bus_id, exception_date, exception_type]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Validate bus belongs to admin
        try:
            bus = Bus.objects.get(owner=request.user, bus_id=bus_id)
        except Bus.DoesNotExist:
            return JsonResponse({'error': 'Bus not found for this admin'}, status=404)
        
        # Parse exception date
        from datetime import datetime
        try:
            exception_date_obj = datetime.strptime(exception_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # Validate override values if provided
        override_route = None
        override_driver = None
        override_start_time_obj = None
        override_end_time_obj = None
        
        if override_route_id:
            try:
                override_route = Route.objects.get(owner=request.user, route_id=override_route_id)
            except Route.DoesNotExist:
                return JsonResponse({'error': 'Override route not found'}, status=404)
        
        if override_driver_id:
            try:
                override_driver = Driver.objects.get(owner=request.user, driver_id=override_driver_id)
            except Driver.DoesNotExist:
                return JsonResponse({'error': 'Override driver not found'}, status=404)
        
        if override_start_time:
            try:
                override_start_time_obj = datetime.strptime(override_start_time, '%H:%M').time()
            except ValueError:
                return JsonResponse({'error': 'Invalid start time format. Use HH:MM'}, status=400)
        
        if override_end_time:
            try:
                override_end_time_obj = datetime.strptime(override_end_time, '%H:%M').time()
            except ValueError:
                return JsonResponse({'error': 'Invalid end time format. Use HH:MM'}, status=400)
        
        # Create exception
        exception = ScheduleException.objects.create(
            owner=request.user,
            bus=bus,
            exception_date=exception_date_obj,
            exception_type=exception_type,
            override_route=override_route,
            override_driver=override_driver,
            override_start_time=override_start_time_obj,
            override_end_time=override_end_time_obj,
            reason=reason,
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Schedule exception created successfully',
            'exception': {
                'id': exception.id,
                'bus_id': exception.bus.bus_id,
                'exception_date': exception.exception_date.isoformat(),
                'exception_type': exception.exception_type,
                'reason': exception.reason,
                'override_route_id': exception.override_route.route_id if exception.override_route else None,
                'override_driver_id': exception.override_driver.driver_id if exception.override_driver else None,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_list_schedule_exceptions(request):
    """List schedule exceptions"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        exceptions = ScheduleException.objects.filter(
            owner=request.user
        ).select_related('bus', 'override_route', 'override_driver')
        
        exceptions_data = []
        for exception in exceptions:
            exceptions_data.append({
                'id': exception.id,
                'bus': {
                    'bus_id': exception.bus.bus_id,
                    'bus_number': exception.bus.bus_number,
                },
                'exception_date': exception.exception_date.isoformat(),
                'exception_type': exception.exception_type,
                'exception_type_display': exception.get_exception_type_display(),
                'reason': exception.reason,
                'override_route': {
                    'route_id': exception.override_route.route_id,
                    'name': exception.override_route.name,
                } if exception.override_route else None,
                'override_driver': {
                    'driver_id': exception.override_driver.driver_id,
                    'name': exception.override_driver.name,
                } if exception.override_driver else None,
                'override_start_time': exception.override_start_time.strftime('%H:%M') if exception.override_start_time else None,
                'override_end_time': exception.override_end_time.strftime('%H:%M') if exception.override_end_time else None,
                'is_active': exception.is_active,
                'created_at': exception.created_at.isoformat(),
            })
        
        return JsonResponse({
            'status': 'success',
            'exceptions': exceptions_data,
            'count': len(exceptions_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_get_current_schedules(request):
    """Get current active schedules for all buses"""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        
        buses = Bus.objects.filter(owner=request.user, is_active=True)
        
        current_schedules = []
        for bus in buses:
            current_schedule = bus.get_current_schedule()
            if current_schedule:
                schedule_data = {
                    'bus_id': bus.bus_id,
                    'bus_number': bus.bus_number,
                    'schedule_type': current_schedule['type'],
                    'route': {
                        'route_id': current_schedule['route'].route_id,
                        'name': current_schedule['route'].name,
                    } if current_schedule['route'] else None,
                }
                
                if current_schedule['type'] == 'schedule' and current_schedule.get('driver'):
                    schedule_data['driver'] = {
                        'driver_id': current_schedule['driver'].driver_id,
                        'name': current_schedule['driver'].name,
                        'mobile': current_schedule['driver'].mobile,
                    }
                elif current_schedule['type'] == 'static':
                    driver_info = bus.get_effective_driver_info()
                    schedule_data['driver_static'] = {
                        'name': driver_info.get('name', ''),
                        'mobile': driver_info.get('mobile', ''),
                    }
                
                current_schedules.append(schedule_data)
        
        return JsonResponse({
            'status': 'success',
            'current_schedules': current_schedules,
            'count': len(current_schedules),
            'generated_at': timezone.now().isoformat(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def check_schedule_conflicts(user, bus, driver, start_time, end_time, days_of_week, effective_from, effective_to):
    """
    Check for schedule conflicts between buses and drivers.
    Returns an error message if conflicts are found, None otherwise.
    """
    from django.db.models import Q
    from datetime import date
    
    # If no effective_to date provided, set a far future date for comparison
    if effective_to is None:
        from datetime import date
        effective_to = date(2099, 12, 31)
    
    # Create a list of weekday numbers from the days_of_week list
    # Assume days_of_week is a list like ['monday', 'tuesday', ...] or [0, 1, 2, ...]
    if days_of_week:
        # Convert text days to numbers if needed
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        weekday_numbers = []
        for day in days_of_week:
            if isinstance(day, str):
                weekday_numbers.append(day_mapping.get(day.lower()))
            else:
                weekday_numbers.append(day)
        # Remove None values in case of invalid day names
        weekday_numbers = [d for d in weekday_numbers if d is not None]
    else:
        weekday_numbers = []
    
    # Build base query for overlapping schedules within the same time period
    base_query = Q(
        owner=user,
        is_active=True,
        # Date range overlap check
        effective_from__lte=effective_to,
        effective_to__gte=effective_from  # This handles None effective_to by using the far future date
    )
    
    # Add time overlap check
    time_overlap_query = Q(
        # Time ranges overlap if: start1 < end2 AND start2 < end1
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    
    # Check for bus conflicts - simplified for SQLite compatibility
    bus_conflicts = Schedule.objects.filter(
        base_query & time_overlap_query & Q(bus=bus)
    )
    
    # Manual check for day overlap since SQLite doesn't support contains lookup
    if weekday_numbers and bus_conflicts.exists():
        for schedule in bus_conflicts:
            if any(day in schedule.days_of_week for day in weekday_numbers):
                return f"Bus {bus.bus_id} is already scheduled during this time in schedule '{schedule.name}'"
    elif bus_conflicts.exists():
        conflicting_schedule = bus_conflicts.first()
        return f"Bus {bus.bus_id} is already scheduled during this time in schedule '{conflicting_schedule.name}'"
    
    # Check for driver conflicts (if driver is provided)
    if driver:
        driver_conflicts = Schedule.objects.filter(
            base_query & time_overlap_query & Q(driver=driver)
        )
        
        # Manual check for day overlap
        if weekday_numbers and driver_conflicts.exists():
            for schedule in driver_conflicts:
                if any(day in schedule.days_of_week for day in weekday_numbers):
                    return f"Driver {driver.name} is already scheduled during this time in schedule '{schedule.name}'"
        elif driver_conflicts.exists():
            conflicting_schedule = driver_conflicts.first()
            return f"Driver {driver.name} is already scheduled during this time in schedule '{conflicting_schedule.name}'"

    
    # Additional validation: Check for schedule exceptions that might conflict
    # This is a simplified check - you might want to make it more sophisticated
    exception_conflicts = ScheduleException.objects.filter(
        owner=user,
        is_active=True,
        bus=bus,
        exception_date__gte=effective_from,
        exception_date__lte=effective_to,
        exception_type='cancelled'
    )
    
    if exception_conflicts.exists():
        # This is informational rather than blocking
        pass  # Could add warning logic here
    
    # No conflicts found
    return None


    
@csrf_exempt
def device_update_location(request):
    """
    POST JSON: {"bus_id":"bus123","latitude":12.34,"longitude":56.78,"speed":40.2,"heading":180}
    """
    if request.method != "POST":
        return JsonResponse({"detail": "only POST allowed"}, status=405)

    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({"detail": "invalid json"}, status=400)

    bus_id = payload.get("bus_id")
    lat = payload.get("latitude")
    lng = payload.get("longitude")
    speed = payload.get("speed", 0.0)
    heading = payload.get("heading", 0.0)

    if not bus_id or lat is None or lng is None:
        return JsonResponse({"detail": "missing fields"}, status=400)

    try:
        bus = Bus.objects.get(bus_id=bus_id)
    except Bus.DoesNotExist:
        return JsonResponse({"detail": "bus not found"}, status=404)

    bl = BusLocation.objects.create(
        bus=bus,
        latitude=lat,
        longitude=lng,
        speed=speed,
        heading=heading
    )
    # post_save signal will push to Firebase
    return JsonResponse({"status": "ok", "id": bl.id})