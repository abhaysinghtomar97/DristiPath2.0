"""
URL configuration for mytrackingproject project.

Custom routing to simple HTML pages served from the project root.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse
from tracking_app import views as tracking_views
from django.shortcuts import render
import os

# Public pages rendered via templates

def serve_index(request):
    return render(request, 'index.html')


def serve_select(request):
    return render(request, 'select_type.html')


def serve_auth(request):
    return render(request, 'auth.html')


def serve_user_dashboard(request):
    return render(request, 'user_dashboard.html')

# Admin dashboard (already protected by view)

def serve_admin_dashboard(request):
    return tracking_views.admin_dashboard(request)

# Debug page

def serve_debug_test(request):
    return _serve_html('debug_test.html')

urlpatterns = [
    path('', serve_index, name='home'),
    path('select/', serve_select, name='select_type'),
    path('auth/', serve_auth, name='auth'),
    path('user/', serve_user_dashboard, name='user_dashboard'),

    path('admin_panel/', tracking_views.admin_dashboard, name='admin_panel'),
    path('debug/', serve_debug_test, name='debug_test'),
    path('admin/', admin.site.urls),
    path('api/', include('tracking_app.urls')),
]
