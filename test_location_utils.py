#!/usr/bin/env python
"""
Test script to validate location utility functions work correctly
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mytrackingproject.settings')
django.setup()

from tracking_app.location_utils import get_location_name, get_route_display_name
from tracking_app.models import Route

def test_location_utils():
    print("🧪 Testing Location Utilities...")
    
    # Test predefined locations
    print("\n📍 Testing Predefined Locations:")
    test_coords = [
        (26.4499, 80.3319, "Kanpur Central"),
        (26.4670, 80.3214, "PSIT Kanpur"), 
        (28.6139, 77.2090, "New Delhi"),
        (19.0760, 72.8777, "Mumbai Central")
    ]
    
    for lat, lng, expected in test_coords:
        result = get_location_name(lat, lng)
        status = "✅" if expected in result else "⚠️"
        print(f"{status} {lat}, {lng} -> {result}")
    
    # Test coordinates that don't match predefined locations (should fall back to reverse geocoding or coordinates)
    print("\n🌍 Testing Fallback Coordinates:")
    fallback_coords = [
        (26.5000, 80.4000),  # Near Kanpur but not exact
        (28.7000, 77.3000),  # Near Delhi but not exact
    ]
    
    for lat, lng in fallback_coords:
        result = get_location_name(lat, lng)
        print(f"📍 {lat}, {lng} -> {result}")
    
    # Test route display names
    print("\n🛣️ Testing Route Display Names:")
    
    # Create a test route
    try:
        test_route = Route.objects.create(
            route_id='TEST-ROUTE',
            name='Test Route',
            start_location='Kanpur Central',
            end_location='PSIT Kanpur',
            description='Test route for validation'
        )
        
        route_display = get_route_display_name(test_route)
        print(f"✅ Route display: {route_display}")
        
        # Clean up
        test_route.delete()
        print("🗑️ Cleaned up test route")
        
    except Exception as e:
        print(f"⚠️ Route test error: {e}")
    
    print("\n✨ Location utilities test completed!")

if __name__ == "__main__":
    test_location_utils()
