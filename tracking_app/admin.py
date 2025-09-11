from django.contrib import admin
from .models import Route, Bus, BusLocation, BusStop, UserLocation

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


