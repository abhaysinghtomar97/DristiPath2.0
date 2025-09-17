from django.contrib import admin
from .models import Route, Bus, BusLocation, BusStop, UserLocation, Driver, Schedule, ScheduleException

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("route_id", "name", "is_active", "created_at")
    search_fields = ("route_id", "name")

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ("bus_id", "bus_number", "route", "driver_name", "capacity", "is_active")
    search_fields = ("bus_id", "bus_number", "driver_name", "route__name")
    list_filter = ("is_active", "route")

@admin.register(BusLocation)
class BusLocationAdmin(admin.ModelAdmin):
    list_display = ("bus", "latitude", "longitude", "speed", "heading", "last_updated")
    search_fields = ("bus__bus_id",)
    list_filter = ("last_updated",)

@admin.register(BusStop)
class BusStopAdmin(admin.ModelAdmin):
    list_display = ("stop_id", "name", "latitude", "longitude", "is_active")
    search_fields = ("stop_id", "name")
    list_filter = ("is_active",)

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ("user", "session_id", "latitude", "longitude", "accuracy", "last_updated")
    search_fields = ("user__username", "session_id")
    list_filter = ("last_updated",)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("driver_id", "name", "mobile", "license_number", "is_active", "owner")
    search_fields = ("driver_id", "name", "mobile", "license_number")
    list_filter = ("is_active", "owner")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("schedule_id", "name", "bus", "route", "driver", "start_time", "end_time", "is_active", "owner")
    search_fields = ("schedule_id", "name", "bus__bus_number", "route__name")
    list_filter = ("is_active", "owner", "days_of_week", "effective_from")
    date_hierarchy = "effective_from"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

@admin.register(ScheduleException)
class ScheduleExceptionAdmin(admin.ModelAdmin):
    list_display = ("bus", "exception_date", "exception_type", "override_route", "override_driver", "is_active", "owner")
    search_fields = ("bus__bus_number", "reason")
    list_filter = ("exception_type", "is_active", "owner", "exception_date")
    date_hierarchy = "exception_date"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)
