from django.db import models
from django.utils import timezone

class TrafficSign(models.Model):
    """Model to store detected traffic signs from sensors"""
    SIGN_TYPES = [
        ('speed_limit', 'Speed Limit'),
        ('no_horn', 'No Horn'),
        ('stop', 'Stop Sign'),
        ('yield', 'Yield Sign'),
        ('one_way', 'One Way'),
        ('no_parking', 'No Parking'),
        ('other', 'Other'),
    ]
    
    sign_type = models.CharField(max_length=20, choices=SIGN_TYPES)
    sign_value = models.CharField(max_length=50, blank=True, null=True)  # e.g., "40" for speed limit
    detected_at = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_sign_type_display()}: {self.sign_value}"

class Vehicle(models.Model):
    """Model to store vehicle information"""
    VEHICLE_TYPES = [
        ('two_wheeler', 'Two Wheeler'),
        ('four_wheeler', 'Four Wheeler'),
        ('commercial', 'Commercial Vehicle'),
    ]
    
    vehicle_id = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    registration_number = models.CharField(max_length=20, blank=True, null=True)
    owner_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.vehicle_id} - {self.get_vehicle_type_display()}"
    
    @property
    def total_violations(self):
        """Calculate total violations for this vehicle"""
        return ComplianceRecord.objects.filter(
            vehicle=self,
            violation_type__in=['speed_violation', 'horn_violation', 'seatbelt_violation']
        ).count()
    
    @property
    def total_trips(self):
        """Calculate total trips for this vehicle"""
        return ComplianceRecord.objects.filter(
            vehicle=self
        ).count()
    
    @property
    def compliance_rate(self):
        """Calculate compliance rate percentage"""
        total_trips = self.total_trips
        if total_trips == 0:
            return 100.0
        violations = self.total_violations
        return round(((total_trips - violations) / total_trips) * 100, 2)
    
    @property
    def average_compliance_score(self):
        """Calculate average compliance score"""
        records = ComplianceRecord.objects.filter(
            vehicle=self
        )
        if not records.exists():
            return 100.0
        total_score = sum(record.compliance_score for record in records)
        return round(total_score / records.count(), 2)
    
    @property
    def qualifies_for_leaderboard(self):
        """Check if vehicle qualifies for leaderboard (minimum 3 entries)"""
        return self.total_trips >= 3

class ManualTrafficSign(models.Model):
    """Model for manually entering traffic sign data with vehicle information"""
    SIGN_TYPES = [
        ('speed_limit', 'Speed Limit'),
        ('no_horn', 'No Horn'),
        ('four_wheeler', 'Four Wheeler'),
        ('seatbelt', 'Seatbelt'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, help_text="Select the vehicle", null=True, blank=True)
    sign_type = models.CharField(max_length=20, choices=SIGN_TYPES, help_text="Select the type of traffic sign")
    sign_value = models.CharField(max_length=50, blank=True, null=True, help_text="Enter the sign value (e.g., 40 for speed limit, 'Yes' for no horn)")
    drive_value = models.IntegerField(blank=True, null=True, help_text="Enter the actual driving value (e.g., actual speed)")
    location = models.CharField(max_length=200, blank=True, null=True, help_text="Location of the traffic sign")
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        vehicle_info = f"{self.vehicle.vehicle_id}" if self.vehicle else "No Vehicle"
        if self.sign_type == 'speed_limit':
            return f"{vehicle_info} - Speed Limit: {self.sign_value} km/h, Drive: {self.drive_value} km/h at {self.location}"
        elif self.sign_type == 'no_horn':
            return f"{vehicle_info} - No Horn: {self.sign_value}, Drive: {self.drive_value} at {self.location}"
        elif self.sign_type == 'four_wheeler':
            return f"{vehicle_info} - Four Wheeler: {self.sign_value}, Drive: {self.drive_value} at {self.location}"
        elif self.sign_type == 'seatbelt':
            return f"{vehicle_info} - Seatbelt: {self.sign_value}, Drive: {self.drive_value} at {self.location}"
        return f"{vehicle_info} - {self.get_sign_type_display()}: {self.sign_value}, Drive: {self.drive_value} at {self.location}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.sign_type == 'speed_limit':
            if not self.sign_value:
                raise ValidationError('Speed limit value is required for speed limit signs')
            try:
                int(self.sign_value)
            except ValueError:
                raise ValidationError('Speed limit value must be a number')
        elif self.sign_type in ['no_horn', 'four_wheeler', 'seatbelt']:
            if not self.sign_value:
                raise ValidationError(f'{self.get_sign_type_display()} value is required')

class ComplianceRecord(models.Model):
    """Model to store compliance data for each traffic sign encounter"""
    VIOLATION_TYPES = [
        ('speed_violation', 'Speed Violation'),
        ('horn_violation', 'Horn Violation'),
        ('seatbelt_violation', 'Seatbelt Violation'),
        ('stop_violation', 'Stop Sign Violation'),
        ('no_violation', 'No Violation'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True)
    traffic_sign = models.ForeignKey(TrafficSign, on_delete=models.CASCADE)
    
    # Speed-related fields
    speed_limit = models.IntegerField(null=True, blank=True)  # from traffic sign
    actual_speed = models.IntegerField(null=True, blank=True)  # from vehicle sensor
    
    # Horn-related fields
    no_horn_zone = models.BooleanField(default=False)  # from traffic sign
    horn_applied = models.BooleanField(default=False)  # from vehicle sensor
    
    # Seatbelt-related fields (for four-wheelers)
    seatbelt_required = models.BooleanField(default=False)  # based on vehicle type
    seatbelt_worn = models.BooleanField(default=False)  # from vehicle sensor
    
    # Violation tracking
    violation_type = models.CharField(max_length=20, choices=VIOLATION_TYPES, default='no_violation')
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')
    violation_description = models.TextField(blank=True, null=True)
    
    # Timestamps
    recorded_at = models.DateTimeField(default=timezone.now)
    
    # Compliance score (0-100)
    compliance_score = models.IntegerField(default=100)
    
    def __str__(self):
        vehicle_id = self.vehicle.vehicle_id if self.vehicle else "No Vehicle"
        return f"Compliance {self.id} - {vehicle_id} - {self.get_violation_type_display()}"
    
    def calculate_compliance_score(self):
        """Calculate compliance score based on violations"""
        score = 100
        
        # Speed violation
        if self.speed_limit and self.actual_speed:
            if self.actual_speed > self.speed_limit:
                score -= 20
                if self.actual_speed > self.speed_limit + 20:
                    score -= 10  # additional penalty for excessive speed
        
        # Horn violation
        if self.no_horn_zone and self.horn_applied:
            score -= 15
        
        # Seatbelt violation
        if self.seatbelt_required and not self.seatbelt_worn:
            score -= 25
        
        return max(0, score)
    
    def save(self, *args, **kwargs):
        # Calculate compliance score before saving
        self.compliance_score = self.calculate_compliance_score()
        super().save(*args, **kwargs)

class Leaderboard(models.Model):
    """Model to track vehicle rankings in the leaderboard"""
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE)
    rank = models.IntegerField(default=0, help_text="Current rank in leaderboard")
    total_violations = models.IntegerField(default=0)
    total_trips = models.IntegerField(default=0)
    compliance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    average_compliance_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    total_tokens_earned = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rank']
    
    def __str__(self):
        return f"#{self.rank} - {self.vehicle.vehicle_id} ({self.compliance_rate}% compliance)"
    
    def update_stats(self):
        """Update leaderboard statistics from vehicle data"""
        self.total_violations = self.vehicle.total_violations
        self.total_trips = self.vehicle.total_trips
        self.compliance_rate = self.vehicle.compliance_rate
        self.average_compliance_score = self.vehicle.average_compliance_score
        
        # Get total tokens earned
        reward_token = RewardToken.objects.filter(vehicle=self.vehicle).first()
        self.total_tokens_earned = reward_token.tokens_earned if reward_token else 0
        
        self.save()
    
    @classmethod
    def update_all_rankings(cls):
        """Update rankings for all vehicles in leaderboard"""
        # Get all vehicles with at least 3 compliance records
        vehicles_with_records = Vehicle.objects.filter(
            compliancerecord__isnull=False
        ).annotate(
            trip_count=models.Count('compliancerecord')
        ).filter(
            trip_count__gte=3  # Minimum 3 entries required
        ).distinct()
        
        # Create leaderboard entries for vehicles that don't have them
        for vehicle in vehicles_with_records:
            leaderboard_entry, created = cls.objects.get_or_create(vehicle=vehicle)
            leaderboard_entry.update_stats()
        
        # Update rankings based on:
        # 1. Maximum number of entries (descending)
        # 2. Minimum violations (ascending)
        # 3. Compliance rate (descending)
        leaderboard_entries = cls.objects.all().order_by(
            '-total_trips', 'total_violations', '-compliance_rate'
        )
        
        for rank, entry in enumerate(leaderboard_entries, 1):
            entry.rank = rank
            entry.save()

class RewardToken(models.Model):
    """Model to store reward tokens earned by drivers"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    tokens_earned = models.IntegerField(default=0)
    tokens_spent = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    @property
    def tokens_available(self):
        return self.tokens_earned - self.tokens_spent
    
    def __str__(self):
        return f"Tokens for {self.vehicle.vehicle_id}: {self.tokens_available} available"
