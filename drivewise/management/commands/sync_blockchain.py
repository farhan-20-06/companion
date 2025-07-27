from django.core.management.base import BaseCommand
from django.conf import settings
from drivewise.blockchain_service import blockchain_service
from drivewise.models import Vehicle, ComplianceRecord


class Command(BaseCommand):
    help = 'Sync DriveWise data to blockchain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicles-only',
            action='store_true',
            help='Sync only vehicles to blockchain',
        )
        parser.add_argument(
            '--records-only',
            action='store_true',
            help='Sync only compliance records to blockchain',
        )
        parser.add_argument(
            '--update-leaderboard',
            action='store_true',
            help='Update leaderboard rankings on blockchain',
        )

    def handle(self, *args, **options):
        if not blockchain_service.is_connected():
            self.stdout.write(
                self.style.ERROR('Blockchain not connected. Please check your configuration.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('Blockchain connected successfully!')
        )

        if options['vehicles_only']:
            self.sync_vehicles()
        elif options['records_only']:
            self.sync_records()
        elif options['update_leaderboard']:
            self.update_leaderboard()
        else:
            self.sync_all()

    def sync_vehicles(self):
        """Sync only vehicles to blockchain"""
        self.stdout.write('Syncing vehicles to blockchain...')
        
        vehicles_synced = 0
        for vehicle in Vehicle.objects.all():
            if blockchain_service.sync_vehicle_to_blockchain(vehicle):
                vehicles_synced += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Synced vehicle: {vehicle.vehicle_id}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to sync vehicle: {vehicle.vehicle_id}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Vehicle sync completed: {vehicles_synced} vehicles synced')
        )

    def sync_records(self):
        """Sync only compliance records to blockchain"""
        self.stdout.write('Syncing compliance records to blockchain...')
        
        records_synced = 0
        for record in ComplianceRecord.objects.all():
            if blockchain_service.sync_compliance_record_to_blockchain(record):
                records_synced += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Synced record: {record.id} for {record.vehicle.vehicle_id}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to sync record: {record.id}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Record sync completed: {records_synced} records synced')
        )

    def update_leaderboard(self):
        """Update leaderboard rankings on blockchain"""
        self.stdout.write('Updating blockchain leaderboard...')
        
        if blockchain_service.update_blockchain_leaderboard():
            self.stdout.write(
                self.style.SUCCESS('✓ Blockchain leaderboard updated successfully')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to update blockchain leaderboard')
            )

    def sync_all(self):
        """Sync all data to blockchain"""
        self.stdout.write('Starting full blockchain sync...')
        
        sync_results = blockchain_service.sync_all_data_to_blockchain()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Sync completed: {sync_results["vehicles_synced"]} vehicles, '
                f'{sync_results["records_synced"]} records'
            )
        )
        
        # Update leaderboard
        self.stdout.write('Updating leaderboard rankings...')
        if blockchain_service.update_blockchain_leaderboard():
            self.stdout.write(
                self.style.SUCCESS('✓ Leaderboard updated successfully')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Failed to update leaderboard')
            ) 