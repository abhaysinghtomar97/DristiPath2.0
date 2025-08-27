from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracking_app.models import Route, Bus, BusStop


class Command(BaseCommand):
    help = 'Set up initial demo data for the bus tracking system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new demo data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Bus.objects.all().delete()
            Route.objects.all().delete()
            BusStop.objects.all().delete()

        # Create demo routes
        routes_data = [
            {
                'route_id': 'ROUTE-CENTRAL',
                'name': 'Central Delhi Express',
                'start_location': 'India Gate',
                'end_location': 'Pitampura',
                'description': 'Express route covering central Delhi landmarks'
            },
            {
                'route_id': 'ROUTE-SOUTH',
                'name': 'South Delhi Route',
                'start_location': 'Noida Sector 18',
                'end_location': 'Connaught Place',
                'description': 'Route connecting Noida to central Delhi'
            },
            {
                'route_id': 'ROUTE-NORTH',
                'name': 'North Delhi Circular',
                'start_location': 'Delhi University',
                'end_location': 'India Gate',
                'description': 'Circular route covering north Delhi areas'
            },
            {
                'route_id': 'ROUTE-AIRPORT',
                'name': 'Airport Express',
                'start_location': 'IGI Airport',
                'end_location': 'Karol Bagh',
                'description': 'High-speed airport connectivity route'
            },
            {
                'route_id': 'ROUTE-EAST',
                'name': 'East Delhi Connect',
                'start_location': 'Rajouri Garden',
                'end_location': 'Lajpat Nagar',
                'description': 'Route connecting east and west Delhi'
            }
        ]

        self.stdout.write('Creating demo routes...')
        for route_data in routes_data:
            route, created = Route.objects.get_or_create(
                route_id=route_data['route_id'],
                defaults=route_data
            )
            if created:
                self.stdout.write(f'✓ Created route: {route.route_id}')
            else:
                self.stdout.write(f'- Route already exists: {route.route_id}')

        # Create demo bus stops
        bus_stops_data = [
            {'stop_id': 'STOP-001', 'name': 'India Gate', 'latitude': 28.6139, 'longitude': 77.2090, 'routes': ['ROUTE-CENTRAL', 'ROUTE-NORTH']},
            {'stop_id': 'STOP-002', 'name': 'Connaught Place', 'latitude': 28.6289, 'longitude': 77.2065, 'routes': ['ROUTE-CENTRAL', 'ROUTE-SOUTH', 'ROUTE-NORTH', 'ROUTE-EAST']},
            {'stop_id': 'STOP-003', 'name': 'Karol Bagh', 'latitude': 28.6448, 'longitude': 77.2167, 'routes': ['ROUTE-CENTRAL', 'ROUTE-NORTH', 'ROUTE-AIRPORT', 'ROUTE-EAST']},
            {'stop_id': 'STOP-004', 'name': 'Rohini Sector 3', 'latitude': 28.6562, 'longitude': 77.2410, 'routes': ['ROUTE-CENTRAL', 'ROUTE-NORTH']},
            {'stop_id': 'STOP-005', 'name': 'Pitampura', 'latitude': 28.6692, 'longitude': 77.2285, 'routes': ['ROUTE-CENTRAL']},
            {'stop_id': 'STOP-006', 'name': 'Noida Sector 18', 'latitude': 28.5355, 'longitude': 77.3910, 'routes': ['ROUTE-SOUTH', 'ROUTE-AIRPORT']},
            {'stop_id': 'STOP-007', 'name': 'Lajpat Nagar', 'latitude': 28.5244, 'longitude': 77.1855, 'routes': ['ROUTE-SOUTH', 'ROUTE-EAST']},
            {'stop_id': 'STOP-008', 'name': 'Safdarjung', 'latitude': 28.5535, 'longitude': 77.2588, 'routes': ['ROUTE-SOUTH']},
            {'stop_id': 'STOP-009', 'name': 'Delhi University', 'latitude': 28.7041, 'longitude': 77.1025, 'routes': ['ROUTE-NORTH']},
            {'stop_id': 'STOP-010', 'name': 'Azadpur', 'latitude': 28.6923, 'longitude': 77.1756, 'routes': ['ROUTE-NORTH']},
            {'stop_id': 'STOP-011', 'name': 'IGI Airport Terminal 3', 'latitude': 28.5562, 'longitude': 77.1000, 'routes': ['ROUTE-AIRPORT']},
            {'stop_id': 'STOP-012', 'name': 'Rajouri Garden', 'latitude': 28.6507, 'longitude': 77.2334, 'routes': ['ROUTE-EAST']},
        ]

        self.stdout.write('Creating demo bus stops...')
        for stop_data in bus_stops_data:
            routes_for_stop = stop_data.pop('routes')
            bus_stop, created = BusStop.objects.get_or_create(
                stop_id=stop_data['stop_id'],
                defaults=stop_data
            )
            
            if created:
                # Add routes to the bus stop
                for route_id in routes_for_stop:
                    try:
                        route = Route.objects.get(route_id=route_id)
                        bus_stop.routes.add(route)
                    except Route.DoesNotExist:
                        pass
                self.stdout.write(f'✓ Created bus stop: {bus_stop.stop_id}')
            else:
                self.stdout.write(f'- Bus stop already exists: {bus_stop.stop_id}')

        # Create demo buses
        buses_data = [
            {'bus_id': 'BUS-001', 'bus_number': 'DL-1234', 'route_id': 'ROUTE-CENTRAL', 'driver_name': 'Ram Kumar', 'capacity': 45},
            {'bus_id': 'BUS-002', 'bus_number': 'DL-5678', 'route_id': 'ROUTE-SOUTH', 'driver_name': 'Suresh Singh', 'capacity': 50},
            {'bus_id': 'BUS-003', 'bus_number': 'DL-9012', 'route_id': 'ROUTE-NORTH', 'driver_name': 'Ajay Sharma', 'capacity': 40},
            {'bus_id': 'BUS-004', 'bus_number': 'DL-3456', 'route_id': 'ROUTE-AIRPORT', 'driver_name': 'Vikash Gupta', 'capacity': 55},
            {'bus_id': 'BUS-005', 'bus_number': 'DL-7890', 'route_id': 'ROUTE-EAST', 'driver_name': 'Mohit Verma', 'capacity': 48},
        ]

        self.stdout.write('Creating demo buses...')
        for bus_data in buses_data:
            route_id = bus_data.pop('route_id')
            try:
                route = Route.objects.get(route_id=route_id)
                bus, created = Bus.objects.get_or_create(
                    bus_id=bus_data['bus_id'],
                    defaults={**bus_data, 'route': route}
                )
                if created:
                    self.stdout.write(f'✓ Created bus: {bus.bus_id} - {bus.bus_number}')
                else:
                    self.stdout.write(f'- Bus already exists: {bus.bus_id}')
            except Route.DoesNotExist:
                self.stdout.write(f'✗ Route {route_id} not found for bus {bus_data["bus_id"]}')

        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write('✓ Created admin user (username: admin, password: admin123)')
        else:
            self.stdout.write('- Admin user already exists')

        self.stdout.write(
            self.style.SUCCESS('Demo data setup complete!')
        )
        self.stdout.write('You can now:')
        self.stdout.write('1. Run the bus simulator: python bus_simulator.py')
        self.stdout.write('2. Access the admin panel at /admin/ (admin/admin123)')
        self.stdout.write('3. View the tracking interface at /')
        self.stdout.write('4. Use the admin dashboard at /admin_panel/')
