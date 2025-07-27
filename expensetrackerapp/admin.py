from django.contrib import admin
from .models import TrafficSign, Vehicle, DrivingSession, ComplianceRecord, RewardToken

@admin.register(TrafficSign)
class TrafficSignAdmin(admin.ModelAdmin):
    list_display = ('sign_type', 'sign_value', 'detected_at', 'location', 'is_active')
    list_filter = ('sign_type', 'is_active', 'detected_at')
    search_fields = ('sign_type', 'sign_value', 'location')
    ordering = ('-detected_at',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_id', 'vehicle_type', 'registration_number', 'owner_name', 'created_at')
    list_filter = ('vehicle_type', 'created_at')
    search_fields = ('vehicle_id', 'registration_number', 'owner_name')
    ordering = ('-created_at',)

@admin.register(DrivingSession)
class DrivingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'session_start', 'session_end', 'is_active')
    list_filter = ('is_active', 'session_start')
    search_fields = ('vehicle__vehicle_id',)
    ordering = ('-session_start',)

@admin.register(ComplianceRecord)
class ComplianceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'traffic_sign', 'violation_type', 'severity', 'compliance_score', 'recorded_at')
    list_filter = ('violation_type', 'severity', 'recorded_at')
    search_fields = ('vehicle__vehicle_id', 'traffic_sign__sign_type')
    ordering = ('-recorded_at',)
    readonly_fields = ('compliance_score',)

@admin.register(RewardToken)
class RewardTokenAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'tokens_earned', 'tokens_spent', 'tokens_available', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('vehicle__vehicle_id',)
    readonly_fields = ('tokens_available',)
