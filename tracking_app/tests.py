from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from .models import Bus, Route, BusLocation, UserLocation
from .location_utils import get_location_name, get_route_display_name


class BusModelTests(TestCase):
    """Test the Bus model with new fields"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )
        self.route = Route.objects.create(
            owner=self.user,
            route_id='TEST-001',
            name='Test Route',
            start_location='Test Start',
            end_location='Test End'
        )
    
    def test_bus_creation_with_new_fields(self):
        """Test creating a bus with new driver_mobile and current_speed fields"""
        bus = Bus.objects.create(
            owner=self.user,
            bus_id='BUS-001',
            bus_number='TN-01-AA-1234',
            route=self.route,
            driver_name='John Doe',
            driver_mobile='9876543210',
            current_speed=45.5,
            capacity=50
        )
        
        self.assertEqual(bus.driver_mobile, '9876543210')
        self.assertEqual(bus.current_speed, 45.5)
        self.assertEqual(bus.capacity, 50)
        
    def test_bus_defaults(self):
        """Test default values for new fields"""
        bus = Bus.objects.create(
            owner=self.user,
            bus_id='BUS-002',
            bus_number='TN-01-BB-5678',
            route=self.route
        )
        
        self.assertEqual(bus.driver_mobile, '')
        self.assertEqual(bus.current_speed, 0.0)
        self.assertEqual(bus.capacity, 50)


class BusSearchAPITests(TestCase):
    """Test the new bus search functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )
        self.route = Route.objects.create(
            owner=self.user,
            route_id='ROUTE-001',
            name='Main Route',
            start_location='Station A',
            end_location='Station B'
        )
        self.bus = Bus.objects.create(
            owner=self.user,
            bus_id='BUS-001',
            bus_number='DL-123',
            route=self.route,
            driver_name='Driver One',
            driver_mobile='9876543210',
            current_speed=30.0
        )
    
    def test_bus_search_by_number(self):
        """Test searching buses by number"""
        response = self.client.get('/api/bus/search/', {'q': 'DL-123'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['buses']), 1)
        self.assertEqual(data['buses'][0]['bus_number'], 'DL-123')
    
    def test_bus_search_by_route(self):
        """Test searching buses by route"""
        response = self.client.get('/api/search_buses/', {'q': 'Main Route'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['buses']), 1)


class NearestBusOptimizationTests(TestCase):
    """Test the optimized nearest bus functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True
        )
        self.route = Route.objects.create(
            owner=self.user,
            route_id='ROUTE-001',
            name='Test Route',
            start_location='Start',
            end_location='End'
        )
        self.bus = Bus.objects.create(
            owner=self.user,
            bus_id='BUS-001',
            bus_number='TN-123',
            route=self.route,
            driver_name='Test Driver',
            driver_mobile='9876543210'
        )
        # Create a bus location
        BusLocation.objects.create(
            bus=self.bus,
            latitude=28.6139,
            longitude=77.2090,
            speed=25.5
        )
    
    def test_find_nearest_buses_optimized(self):
        """Test the optimized nearest buses endpoint"""
        response = self.client.get('/api/find_nearest_buses/', {
            'lat': '28.6139',
            'lng': '77.2090',
            'radius': '5'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('nearest_buses', data)
        # Should include driver mobile and current speed
        if data['nearest_buses']:
            bus_data = data['nearest_buses'][0]
            self.assertIn('driver_mobile', bus_data)
            self.assertIn('current_speed', bus_data)


class AdminAnalyticsTests(TestCase):
    """Test the fixed admin analytics"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.route = Route.objects.create(
            owner=self.admin_user,
            route_id='ROUTE-001',
            name='Admin Route',
            start_location='A',
            end_location='B'
        )
        self.bus = Bus.objects.create(
            owner=self.admin_user,
            bus_id='ADMIN-BUS-001',
            bus_number='ADM-123',
            route=self.route
        )
    
    def test_analytics_active_vehicles_count(self):
        """Test that analytics correctly counts active vehicles with recent location updates"""
        self.client.login(username='admin', password='adminpass123')
        
        # Create a location first
        location = BusLocation.objects.create(
            bus=self.bus,
            latitude=28.6139,
            longitude=77.2090,
            speed=20.0
        )
        
        # Update the timestamp to be recent (within last 5 minutes) using update() to bypass auto_now
        recent_time = timezone.now() - timedelta(minutes=2)
        BusLocation.objects.filter(id=location.id).update(last_updated=recent_time)
        
        response = self.client.get('/api/admin/analytics/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        # Should count the bus as active since it has recent location update
        self.assertEqual(data['summary']['active_recent'], 1)
        
    def test_analytics_inactive_vehicles_count(self):
        """Test that analytics correctly excludes vehicles without recent updates"""
        self.client.login(username='admin', password='adminpass123')
        
        # Create a location first
        location = BusLocation.objects.create(
            bus=self.bus,
            latitude=28.6139,
            longitude=77.2090,
            speed=20.0
        )
        
        # Update the timestamp to be old (more than 5 minutes ago) using update() to bypass auto_now
        old_time = timezone.now() - timedelta(minutes=10)
        BusLocation.objects.filter(id=location.id).update(last_updated=old_time)
        
        response = self.client.get('/api/admin/analytics/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        # Should not count the bus as active since location update is old
        self.assertEqual(data['summary']['active_recent'], 0)


class LocationUtilsTests(TestCase):
    """Test the location utilities for human-readable names"""
    
    def test_get_location_name_predefined(self):
        """Test getting predefined location names"""
        # Test with Delhi coordinates (predefined)
        location_name = get_location_name(28.6139, 77.2090)
        self.assertEqual(location_name, 'New Delhi')
    
    def test_get_location_name_fallback(self):
        """Test fallback to coordinates when no predefined location"""
        # Test with random coordinates
        location_name = get_location_name(12.9716, 77.5946)
        # Should either return a geocoded name or coordinates
        self.assertTrue(len(location_name) > 0)
    
    def test_get_route_display_name(self):
        """Test route display name generation"""
        route = Route.objects.create(
            route_id='TEST-ROUTE',
            name='Test Route Name',
            start_location='Kanpur',
            end_location='PSIT Kanpur'
        )
        
        display_name = get_route_display_name(route)
        self.assertIn('Kanpur', display_name)
        self.assertIn('PSIT Kanpur', display_name)
        self.assertIn('→', display_name)  # Arrow symbol


class AdminVehicleProfileTests(TestCase):
    """Test the admin vehicle profile functionality"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.route = Route.objects.create(
            owner=self.admin_user,
            route_id='ROUTE-001',
            name='Profile Test Route',
            start_location='Start Point',
            end_location='End Point'
        )
        self.bus = Bus.objects.create(
            owner=self.admin_user,
            bus_id='PROFILE-BUS-001',
            bus_number='PB-123',
            route=self.route,
            driver_name='Profile Test Driver',
            driver_mobile='9876543210',
            current_speed=35.0,
            capacity=45
        )
    
    def test_admin_list_buses_includes_new_fields(self):
        """Test that admin list buses API includes driver mobile and current speed"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/api/admin/list_buses/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['buses']), 1)
        
        bus_data = data['buses'][0]
        self.assertEqual(bus_data['driver_name'], 'Profile Test Driver')
        self.assertIn('bus_number', bus_data)
        self.assertEqual(bus_data['bus_number'], 'PB-123')
