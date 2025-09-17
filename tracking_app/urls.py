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
    path('bus/search/', views.search_buses, name='bus_search'),  # Alternative endpoint for bus search
    path('routes/', views.get_routes, name='get_routes'),
    
    # Authentication APIs
    path('admin/login/', views.admin_authenticate, name='admin_authenticate'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin/signup/', views.admin_signup, name='admin_signup'),
    
    # User Authentication APIs
    path('user/login/', views.user_authenticate, name='user_authenticate'),
    path('user/logout/', views.user_logout_view, name='user_logout'),
    path('user/signup/', views.user_signup, name='user_signup'),
    path('csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    
    # Admin APIs
    path('admin/add_bus/', views.admin_add_bus, name='admin_add_bus'),
    path('admin/list_buses/', views.admin_list_buses, name='admin_list_buses'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin/toggle_bus_status/', views.admin_toggle_bus_status, name='admin_toggle_bus_status'),
    path('admin/add_route/', views.admin_add_route, name='admin_add_route'),
    path('admin/clean_old_locations/', views.admin_clean_old_locations, name='admin_clean_old_locations'),
    path('admin/list_routes/', views.admin_list_routes, name='admin_list_routes'),
    
    # Dynamic Bus Management APIs
    path('admin/update_bus_route/', views.admin_update_bus_route, name='admin_update_bus_route'),
    path('admin/update_bus_driver/', views.admin_update_bus_driver, name='admin_update_bus_driver'),
    path('admin/update_bus_comprehensive/', views.admin_update_bus_comprehensive, name='admin_update_bus_comprehensive'),
    
    # Dynamic Scheduling APIs
    path('admin/add_driver/', views.admin_add_driver, name='admin_add_driver'),
    path('admin/list_drivers/', views.admin_list_drivers, name='admin_list_drivers'),
    path('admin/add_schedule/', views.admin_add_schedule, name='admin_add_schedule'),
    path('admin/list_schedules/', views.admin_list_schedules, name='admin_list_schedules'),
    path('admin/add_schedule_exception/', views.admin_add_schedule_exception, name='admin_add_schedule_exception'),
    path('admin/list_schedule_exceptions/', views.admin_list_schedule_exceptions, name='admin_list_schedule_exceptions'),
    path('admin/get_current_schedules/', views.admin_get_current_schedules, name='admin_get_current_schedules'),
    
    # Web views
    path('dashboard/', views.home, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
