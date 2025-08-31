from django.urls import path
from . import views

urlpatterns = [
    # Bus location APIs
    path('update_location/', views.update_location, name='update_location'),
    path('get_locations/', views.get_locations, name='get_locations'),
    
    # User location & nearest bus APIs
    path('update_user_location/', views.update_user_location, name='update_user_location'),
    path('find_nearest_buses/', views.find_nearest_buses, name='find_nearest_buses'),
    
    # Bus search APIs
    path('search_buses/', views.search_buses, name='search_buses'),
    path('routes/', views.get_routes, name='get_routes'),
    
    # Authentication APIs
    path('admin/login/', views.admin_authenticate, name='admin_authenticate'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin/signup/', views.admin_signup, name='admin_signup'),
    
    # Admin APIs
    path('admin/add_bus/', views.admin_add_bus, name='admin_add_bus'),
    path('admin/list_buses/', views.admin_list_buses, name='admin_list_buses'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin/toggle_bus_status/', views.admin_toggle_bus_status, name='admin_toggle_bus_status'),
    path('admin/add_route/', views.admin_add_route, name='admin_add_route'),
    path('admin/clean_old_locations/', views.admin_clean_old_locations, name='admin_clean_old_locations'),
    
    # Web views
    path('dashboard/', views.home, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
