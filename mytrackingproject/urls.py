"""
URL configuration for mytrackingproject project.

Custom routing to simple HTML pages served from the project root.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse
from tracking_app import views as tracking_views
import os

# Helper to read an HTML file from BASE_DIR

def _serve_html(filename: str) -> HttpResponse:
    path = os.path.join(settings.BASE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse(f'<h1>Page not found</h1><p>Missing {filename}</p>', status=404)

# Public pages

def serve_index(request):
    """Landing page with Get Started button"""
    return _serve_html('index.html')


def serve_select(request):
    """User type selection page"""
    return _serve_html('select_type.html')


def serve_auth(request):
    """Auth page (sign in / sign up) for user or admin depending on query param"""
    return _serve_html('auth.html')


def serve_user_dashboard(request):
    """User dashboard (map + features)"""
    return _serve_html('user_dashboard.html')

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
