# Location utilities for human-readable location names
import requests
from django.conf import settings

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
