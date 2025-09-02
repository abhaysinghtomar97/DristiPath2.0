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
    """Delete BusLocation rows older than N days (default 7) for current admin's vehicles."""
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
        data = json.loads(request.body) if request.body else {}
        days = int(data.get('days', 7))
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = BusLocation.objects.filter(bus__owner=request.user, last_updated__lt=cutoff).delete()
        return JsonResponse({'status': 'success', 'deleted': deleted, 'days': days})
        deleted, _ = BusLocation.objects.filter(last_updated__lt=cutoff).delete()
        return JsonResponse({'status': 'success', 'deleted': deleted, 'days': days})

    except ValueError:
        return JsonResponse({'error': 'Invalid days value'}, status=400)
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
        
        # Buses with activity in last 3 minutes
        recent_bus_ids = BusLocation.objects.filter(bus__owner=request.user, last_updated__gte=three_min_ago).values_list('bus_id', flat=True).distinct()
        active_recent = Bus.objects.filter(owner=request.user, id__in=recent_bus_ids).count()
        
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