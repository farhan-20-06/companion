
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

class DrivingSession(models.Model):
    """Model to store driving session data"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    session_start = models.DateTimeField(default=timezone.now)
    session_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Session {self.id} - {self.vehicle.vehicle_id}"

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
    
    driving_session = models.ForeignKey(DrivingSession, on_delete=models.CASCADE)
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
        return f"Compliance {self.id} - {self.vehicle.vehicle_id} - {self.get_violation_type_display()}"
    
    @property
    def vehicle(self):
        return self.driving_session.vehicle
    
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