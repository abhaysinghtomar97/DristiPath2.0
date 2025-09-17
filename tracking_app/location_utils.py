# Location utilities for human-readable location names
import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import hashlib
import json

# Predefined location mappings for common coordinates
PREDEFINED_LOCATIONS = {
    # Kanpur area locations
    (26.4499, 80.3319): "Kanpur Central",
    (26.4670, 80.3214): "PSIT Kanpur", 
    (26.4775, 80.3707): "Panki Industrial Area",
    (26.4584, 80.3311): "Kanpur Railway Station",
    (26.4478, 80.3463): "IIT Kanpur",
    (26.4733, 80.3022): "Kalyanpur",
    (26.4926, 80.2906): "Barra",
    
    # Delhi area locations  
    (28.6139, 77.2090): "New Delhi",
    (28.6562, 77.2410): "Red Fort",
    (28.5562, 77.1000): "IGI Airport",
    (28.7041, 77.1025): "Delhi University",
    (28.6692, 77.4538): "Ghaziabad",
    (28.4595, 77.0266): "Gurgaon",
    
    # Mumbai area locations
    (19.0760, 72.8777): "Mumbai Central",
    (19.0176, 72.8562): "Gateway of India",
    (19.0896, 72.8656): "Bandra",
    (19.1136, 72.8697): "Andheri",
}

def get_location_name(latitude, longitude, accuracy_threshold=0.01):
    """
    Get human-readable location name for given coordinates.
    First checks predefined locations, then falls back to reverse geocoding.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate  
        accuracy_threshold (float): Distance threshold for predefined location match
        
    Returns:
        str: Human-readable location name
    """
    try:
        # Check predefined locations first
        for (pred_lat, pred_lng), name in PREDEFINED_LOCATIONS.items():
            # Calculate approximate distance (simple euclidean for small distances)
            distance = ((latitude - pred_lat) ** 2 + (longitude - pred_lng) ** 2) ** 0.5
            if distance <= accuracy_threshold:
                return name
        
        # Fall back to reverse geocoding if no predefined match
        return reverse_geocode(latitude, longitude)
        
    except Exception as e:
        print(f"Error getting location name: {e}")
        return f"{latitude:.4f}, {longitude:.4f}"

def reverse_geocode(latitude, longitude):
    """
    Perform reverse geocoding using a free geocoding service.
    Returns human-readable address or formatted coordinates if fails.
    """
    try:
        # Using OpenStreetMap Nominatim (free, no API key required)
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'accept-language': 'en'
        }
        
        headers = {
            'User-Agent': 'DristiPath-Transport-Tracker/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Try to extract meaningful location components
            address = data.get('address', {})
            
            # Priority order for location name selection
            location_parts = []
            
            # Add specific place names
            if address.get('amenity'):
                location_parts.append(address['amenity'])
            elif address.get('building'):
                location_parts.append(address['building'])
            elif address.get('office'):
                location_parts.append(address['office'])
            
            # Add area/neighborhood
            if address.get('neighbourhood'):
                location_parts.append(address['neighbourhood'])
            elif address.get('suburb'):
                location_parts.append(address['suburb'])
            elif address.get('residential'):
                location_parts.append(address['residential'])
                
            # Add city/town
            if address.get('city'):
                location_parts.append(address['city'])
            elif address.get('town'):
                location_parts.append(address['town'])
            elif address.get('village'):
                location_parts.append(address['village'])
                
            # If we have meaningful parts, join them
            if location_parts:
                return ', '.join(location_parts[:2])  # Take max 2 parts to avoid too long
            
            # Fall back to display name
            display_name = data.get('display_name', '')
            if display_name:
                # Take first 2 parts of display name (usually most relevant)
                parts = display_name.split(',')
                return ', '.join(parts[:2]).strip()
                
    except Exception as e:
        print(f"Reverse geocoding failed: {e}")
    
    # Final fallback to coordinates
    return f"{latitude:.4f}, {longitude:.4f}"

def get_route_display_name(route):
    """
    Generate human-readable route name from route object.
    
    Args:
        route: Route model instance
        
    Returns:
        str: Human-readable route name like "Kanpur → PSIT → Panki"
    """
    if not route:
        return "Unknown Route"
        
    start = route.start_location
    end = route.end_location
    
    # If locations are coordinates, convert them
    try:
        # Check if start_location looks like coordinates (contains numbers and comma/space)
        if ',' in start and any(c.isdigit() for c in start):
            coords = start.replace(' ', '').split(',')
            if len(coords) == 2:
                lat, lng = float(coords[0]), float(coords[1])
                start = get_location_name(lat, lng)
    except:
        pass  # Keep original if parsing fails
        
    try:
        # Check if end_location looks like coordinates
        if ',' in end and any(c.isdigit() for c in end):
            coords = end.replace(' ', '').split(',')
            if len(coords) == 2:
                lat, lng = float(coords[0]), float(coords[1])
                end = get_location_name(lat, lng)
    except:
        pass  # Keep original if parsing fails
    
    # Return formatted route name
    if route.name and route.name not in ['Default Simulation Route', 'Unknown']:
        return f"{start} → {end} ({route.name})"
    else:
        return f"{start} → {end}"

def add_predefined_location(latitude, longitude, name):
    """
    Add a new predefined location mapping (for admin use).
    """
    PREDEFINED_LOCATIONS[(latitude, longitude)] = name

# ============= Caching Functions for Performance =============

def get_cache_key(prefix, *args):
    """
    Generate a consistent cache key from prefix and arguments.
    """
    key_data = f"{prefix}:{'_'.join(map(str, args))}"
    # Hash long keys to avoid cache key length limits
    if len(key_data) > 200:
        key_data = hashlib.md5(key_data.encode()).hexdigest()
    return key_data

def cache_route_data(user_id, timeout=300):
    """
    Cache route data for a specific admin user to speed up lookups.
    Default timeout: 5 minutes.
    """
    cache_key = get_cache_key('admin_routes', user_id)
    
    try:
        from .models import Route
        routes = Route.objects.filter(owner_id=user_id, is_active=True).values(
            'id', 'route_id', 'name', 'start_location', 'end_location', 'description'
        )
        route_list = list(routes)
        cache.set(cache_key, route_list, timeout)
        return route_list
    except Exception as e:
        print(f"Error caching route data: {e}")
        return []

def get_cached_routes(user_id):
    """
    Get cached route data for admin user, or fetch and cache if not available.
    """
    cache_key = get_cache_key('admin_routes', user_id)
    routes = cache.get(cache_key)
    
    if routes is None:
        routes = cache_route_data(user_id)
    
    return routes

def cache_driver_data(user_id, timeout=300):
    """
    Cache driver data for a specific admin user to speed up lookups.
    Default timeout: 5 minutes.
    """
    cache_key = get_cache_key('admin_drivers', user_id)
    
    try:
        from .models import Driver
        drivers = Driver.objects.filter(owner_id=user_id, is_active=True).values(
            'id', 'driver_id', 'name', 'mobile', 'license_number', 'email'
        )
        driver_list = list(drivers)
        cache.set(cache_key, driver_list, timeout)
        return driver_list
    except Exception as e:
        print(f"Error caching driver data: {e}")
        return []

def get_cached_drivers(user_id):
    """
    Get cached driver data for admin user, or fetch and cache if not available.
    """
    cache_key = get_cache_key('admin_drivers', user_id)
    drivers = cache.get(cache_key)
    
    if drivers is None:
        drivers = cache_driver_data(user_id)
    
    return drivers

def cache_bus_data(user_id, timeout=60):
    """
    Cache bus data for a specific admin user.
    Shorter timeout (1 minute) since bus data changes more frequently.
    """
    cache_key = get_cache_key('admin_buses', user_id)
    
    try:
        from .models import Bus
        buses = Bus.objects.filter(owner_id=user_id).select_related('route').values(
            'id', 'bus_id', 'bus_number', 'vehicle_type', 'capacity', 'is_active',
            'driver_name', 'driver_mobile', 'route__route_id', 'route__name'
        )
        bus_list = list(buses)
        cache.set(cache_key, bus_list, timeout)
        return bus_list
    except Exception as e:
        print(f"Error caching bus data: {e}")
        return []

def get_cached_buses(user_id):
    """
    Get cached bus data for admin user, or fetch and cache if not available.
    """
    cache_key = get_cache_key('admin_buses', user_id)
    buses = cache.get(cache_key)
    
    if buses is None:
        buses = cache_bus_data(user_id)
    
    return buses

def invalidate_user_cache(user_id, cache_types=None):
    """
    Invalidate cached data for a user.
    
    Args:
        user_id: User ID to invalidate cache for
        cache_types: List of cache types to invalidate. If None, invalidates all.
                    Options: ['routes', 'drivers', 'buses']
    """
    if cache_types is None:
        cache_types = ['routes', 'drivers', 'buses']
    
    cache_keys = []
    if 'routes' in cache_types:
        cache_keys.append(get_cache_key('admin_routes', user_id))
    if 'drivers' in cache_types:
        cache_keys.append(get_cache_key('admin_drivers', user_id))
    if 'buses' in cache_types:
        cache_keys.append(get_cache_key('admin_buses', user_id))
    
    cache.delete_many(cache_keys)

def cache_location_lookup(latitude, longitude, location_name, timeout=3600):
    """
    Cache location lookup results to avoid repeated reverse geocoding.
    Default timeout: 1 hour.
    """
    cache_key = get_cache_key('location', round(latitude, 4), round(longitude, 4))
    cache.set(cache_key, location_name, timeout)

def get_cached_location(latitude, longitude):
    """
    Get cached location name or None if not cached.
    """
    cache_key = get_cache_key('location', round(latitude, 4), round(longitude, 4))
    return cache.get(cache_key)

def cached_reverse_geocode(latitude, longitude):
    """
    Cached version of reverse geocoding.
    """
    # Check cache first
    cached_result = get_cached_location(latitude, longitude)
    if cached_result:
        return cached_result
    
    # Perform geocoding
    result = reverse_geocode(latitude, longitude)
    
    # Cache the result
    cache_location_lookup(latitude, longitude, result)
    
    return result

def get_cached_location_name(latitude, longitude, accuracy_threshold=0.01):
    """
    Cached version of get_location_name function.
    """
    try:
        # Check predefined locations first (these don't need caching)
        for (pred_lat, pred_lng), name in PREDEFINED_LOCATIONS.items():
            distance = ((latitude - pred_lat) ** 2 + (longitude - pred_lng) ** 2) ** 0.5
            if distance <= accuracy_threshold:
                return name
        
        # Use cached reverse geocoding
        return cached_reverse_geocode(latitude, longitude)
        
    except Exception as e:
        print(f"Error getting cached location name: {e}")
        return f"{latitude:.4f}, {longitude:.4f}"
