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
    
    # Admin APIs
    path('admin/add_bus/', views.admin_add_bus, name='admin_add_bus'),
    path('admin/list_buses/', views.admin_list_buses, name='admin_list_buses'),
    
    # Web views
    path('dashboard/', views.home, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
