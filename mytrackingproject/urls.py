"""
URL configuration for mytrackingproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse
from django.shortcuts import render
from tracking_app import views as tracking_views
import os

def serve_index(request):
    """Serve the main tracking interface"""
    index_path = os.path.join(settings.BASE_DIR, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    from django.http import HttpResponse
    return HttpResponse(content, content_type='text/html')

def serve_admin_dashboard(request):
    """Serve the admin dashboard"""
    admin_path = os.path.join(settings.BASE_DIR, 'admin_dashboard.html')
    if os.path.exists(admin_path):
        with open(admin_path, 'r', encoding='utf-8') as f:
            content = f.read()
        from django.http import HttpResponse
        return HttpResponse(content, content_type='text/html')
    else:
        from django.http import HttpResponse
        return HttpResponse('<h1>Admin Dashboard</h1><p>Admin dashboard page not found. Please create admin_dashboard.html</p>')

def serve_debug_test(request):
    """Serve the debug test page"""
    debug_path = os.path.join(settings.BASE_DIR, 'debug_test.html')
    with open(debug_path, 'r', encoding='utf-8') as f:
        content = f.read()
    from django.http import HttpResponse
    return HttpResponse(content, content_type='text/html')

urlpatterns = [
    path('', serve_index, name='home'),
    path('admin_panel/', tracking_views.admin_dashboard, name='admin_panel'),
    path('debug/', serve_debug_test, name='debug_test'),
    path('admin/', admin.site.urls),
    path('api/', include('tracking_app.urls')),
]
