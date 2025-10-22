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
        ("auto", "Auto"),
        ("truck", "Truck"),
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
    
    def get_current_schedule(self, current_datetime=None):
        """Get the currently active schedule for this bus with exception handling"""
        if current_datetime is None:
            current_datetime = timezone.now()
        
        # First check for exceptions on this date
        exception = self.schedule_exceptions.filter(
            exception_date=current_datetime.date(),
            is_active=True
        ).first()
        
        if exception:
            if exception.exception_type in ['cancel', 'maintenance', 'holiday']:
                return None  # No service
            
            # Return exception details as a schedule-like object
            return {
                'type': 'exception',
                'exception': exception,
                'route': exception.override_route or exception.change_route or (exception.schedule.route if exception.schedule else self.route),
                'driver': exception.override_driver or exception.change_driver or (exception.schedule.driver if exception.schedule else None),
                'start_time': exception.override_start_time or (exception.schedule.start_time if exception.schedule else None),
                'end_time': exception.override_end_time or (exception.schedule.end_time if exception.schedule else None)
            }
        
        # No exception, check for active schedules
        active_schedule = self.schedules.filter(
            is_active=True,
            effective_from__lte=current_datetime.date()
        ).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=current_datetime.date())
        ).filter(
            days_of_week__contains=[current_datetime.weekday()]
        ).order_by('-priority', 'start_time').first()
        
        if active_schedule and active_schedule.is_active_now(current_datetime):
            return {
                'type': 'schedule',
                'schedule': active_schedule,
                'route': active_schedule.route,
                'driver': active_schedule.driver,
                'start_time': active_schedule.start_time,
                'end_time': active_schedule.end_time
            }
        
        # Fallback to static assignment
        return {
            'type': 'static',
            'route': self.route,
            'driver': None,
            'driver_name': self.driver_name,
            'driver_mobile': self.driver_mobile
        }
    
    def get_effective_route(self, current_datetime=None):
        """Get the currently effective route (considering schedules and exceptions)"""
        current_schedule = self.get_current_schedule(current_datetime)
        if current_schedule:
            return current_schedule.get('route', self.route)
        return self.route
    
    def get_effective_driver(self, current_datetime=None):
        """Get the currently effective driver (considering schedules and exceptions)"""
        current_schedule = self.get_current_schedule(current_datetime)
        if current_schedule and current_schedule.get('driver'):
            return current_schedule['driver']
        return None
    
    def get_effective_driver_info(self, current_datetime=None):
        """Get driver info including legacy driver_name and driver_mobile"""
        current_schedule = self.get_current_schedule(current_datetime)
        if current_schedule:
            if current_schedule['type'] == 'static':
                return {
                    'name': current_schedule.get('driver_name', ''),
                    'mobile': current_schedule.get('driver_mobile', '')
                }
            elif current_schedule.get('driver'):
                driver = current_schedule['driver']
                return {
                    'name': driver.name,
                    'mobile': driver.mobile,
                    'email': driver.email,
                    'license': driver.license_number
                }
        return {'name': self.driver_name, 'mobile': self.driver_mobile}

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

class Driver(models.Model):
    """Driver information separate from bus assignment"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='owned_drivers')
    driver_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, blank=True, help_text="Driver's contact number")
    license_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'driver_id'], name='unique_driver_per_owner')
        ]
    
    def __str__(self):
        return f"{self.driver_id} - {self.name}"

class Schedule(models.Model):
    """Dynamic scheduling for bus routes and drivers"""
    WEEKDAYS = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_schedules')
    schedule_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100, help_text="Schedule name for easy identification")
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='schedules')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
    
    # Time configuration
    start_time = models.TimeField(help_text="Schedule start time")
    end_time = models.TimeField(help_text="Schedule end time")
    days_of_week = models.JSONField(default=list, help_text="List of weekday numbers (0=Monday, 6=Sunday)")
    
    # Schedule validity period
    effective_from = models.DateField(help_text="Date from which this schedule is effective")
    effective_to = models.DateField(null=True, blank=True, help_text="Date until which this schedule is effective (optional)")
    
    # Priority for overlapping schedules (higher number = higher priority)
    priority = models.IntegerField(default=1, help_text="Priority for resolving conflicting schedules")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'schedule_id'], name='unique_schedule_per_owner')
        ]
        ordering = ['-priority', 'start_time']
    
    def __str__(self):
        days_str = ', '.join([dict(self.WEEKDAYS)[day] for day in self.days_of_week])
        return f"{self.name} - {self.bus.bus_number} ({days_str} {self.start_time}-{self.end_time})"
    
    def is_active_now(self, current_datetime=None):
        """Check if this schedule is currently active"""
        if current_datetime is None:
            current_datetime = timezone.now()
        
        if not self.is_active:
            return False
        
        # Check date range
        current_date = current_datetime.date()
        if current_date < self.effective_from:
            return False
        if self.effective_to and current_date > self.effective_to:
            return False
        
        # Check day of week
        current_weekday = current_datetime.weekday()
        if current_weekday not in self.days_of_week:
            return False
        
        # Check time range
        current_time = current_datetime.time()
        if self.start_time <= self.end_time:
            # Normal time range (e.g., 09:00-17:00)
            return self.start_time <= current_time <= self.end_time
        else:
            # Overnight time range (e.g., 22:00-06:00)
            return current_time >= self.start_time or current_time <= self.end_time
    
    def get_weekdays_display(self):
        """Get a human-readable string of scheduled weekdays"""
        if not self.days_of_week:
            return "No days selected"
        
        day_names = [dict(self.WEEKDAYS)[day][:3] for day in sorted(self.days_of_week)]
        return ', '.join(day_names)

class ScheduleException(models.Model):
    """One-time exceptions to regular schedules (holidays, maintenance, etc.)"""
    EXCEPTION_TYPES = [
        ('override', 'Override - Replace regular schedule'),
        ('cancel', 'Cancel - No service'),
        ('driver_change', 'Driver Change Only'),
        ('route_change', 'Route Change Only'),
        ('maintenance', 'Maintenance - No service'),
        ('holiday', 'Holiday - No service'),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_schedule_exceptions')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='exceptions', null=True, blank=True)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='schedule_exceptions')
    
    # Exception details
    exception_date = models.DateField(help_text="Date of the exception")
    exception_type = models.CharField(max_length=20, choices=EXCEPTION_TYPES)
    
    # Override values (only used for 'override' type)
    override_route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True, help_text="Route for override")
    override_driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True, help_text="Driver for override")
    override_start_time = models.TimeField(null=True, blank=True, help_text="Override start time")
    override_end_time = models.TimeField(null=True, blank=True, help_text="Override end time")
    
    # Change-only values (for driver_change/route_change types)
    change_route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True, related_name='change_exceptions', help_text="New route for change")
    change_driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True, related_name='change_exceptions', help_text="New driver for change")
    
    reason = models.TextField(blank=True, help_text="Reason for the exception")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['exception_date']
    
    def __str__(self):
        return f"{self.bus.bus_number} - {self.get_exception_type_display()} on {self.exception_date}"
    
    def applies_to_datetime(self, current_datetime):
        """Check if this exception applies to the given datetime"""
        if not self.is_active:
            return False
        
        return current_datetime.date() == self.exception_date
