from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from math import radians, cos, sin, asin, sqrt



class Route(models.Model):
    """Route information (per admin owner)"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='owned_routes')
    route_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    start_location = models.CharField(max_length=200)
    end_location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'route_id'], name='unique_route_per_owner')
        ]
    
    def __str__(self):
        return f"{self.route_id} - {self.name}"

class Bus(models.Model):
    """Vehicle information (bus/metro/train/etc.)"""
    VEHICLE_TYPES = [
        ("bus", "Bus"),
        ("metro", "Metro"),
        ("tram", "Tram"),
        ("train", "Train"),
        ("ferry", "Ferry"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='owned_buses')
    bus_id = models.CharField(max_length=50)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='buses')
    driver_name = models.CharField(max_length=100, blank=True)
    driver_mobile = models.CharField(max_length=15, blank=True, help_text="Driver's contact number")
    bus_number = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default="bus")
    capacity = models.IntegerField(default=50)
    current_speed = models.FloatField(default=0.0, help_text="Current speed in km/h")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'bus_id'], name='unique_vehicle_per_owner')
        ]
    
    def __str__(self):
        return f"{self.bus_id} - {self.bus_number} ({self.vehicle_type})"
    
    def get_current_location(self):
        """Get the latest location of this bus"""
        return self.locations.first()  # Latest location

class BusLocation(models.Model):
    """Bus location tracking"""
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0.0)  # Speed in km/h
    heading = models.FloatField(default=0.0)  # Direction in degrees
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"Bus {self.bus.bus_id} - {self.latitude}, {self.longitude}"
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in kilometers"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

class UserLocation(models.Model):
    """User location for finding nearest buses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)  # For anonymous users
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField(default=0.0)  # GPS accuracy in meters
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_updated']
    
    def __str__(self):
        user_info = self.user.username if self.user else f"Session {self.session_id}"
        return f"{user_info} - {self.latitude}, {self.longitude}"
    
    def find_nearest_buses(self, radius_km=5.0, limit=10):
        """Find nearest buses within given radius"""
        from django.db import connection
        
        # Get all active bus locations
        bus_locations = BusLocation.objects.select_related('bus').filter(
            bus__is_active=True
        )
        
        nearby_buses = []
        for bus_location in bus_locations:
            distance = BusLocation.calculate_distance(
                self.latitude, self.longitude,
                bus_location.latitude, bus_location.longitude
            )
            
            if distance <= radius_km:
                nearby_buses.append({
                    'bus': bus_location.bus,
                    'location': bus_location,
                    'distance': round(distance, 2)
                })
        
        # Sort by distance and limit results
        nearby_buses.sort(key=lambda x: x['distance'])
        return nearby_buses[:limit]

class BusStop(models.Model):
    """Bus stops along routes"""
    stop_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    routes = models.ManyToManyField(Route, related_name='stops')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.stop_id} - {self.name}"
