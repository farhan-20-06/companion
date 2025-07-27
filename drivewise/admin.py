from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import TrafficSign, ManualTrafficSign, Vehicle, ComplianceRecord, RewardToken, Leaderboard

class ManualTrafficSignForm(forms.ModelForm):
    """Custom form for ManualTrafficSign with vehicle field"""
    
    class Meta:
        model = ManualTrafficSign
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text based on sign type
        if self.instance and self.instance.sign_type:
            if self.instance.sign_type == 'speed_limit':
                self.fields['sign_value'].help_text = "Enter speed limit value (e.g., 40, 60)"
                self.fields['drive_value'].help_text = "Enter actual speed driven"
            elif self.instance.sign_type == 'no_horn':
                self.fields['sign_value'].help_text = "Enter 'Yes' or 'No' for no horn zone"
                self.fields['drive_value'].help_text = "Enter 1 if horn was used, 0 if not"
            elif self.instance.sign_type == 'four_wheeler':
                self.fields['sign_value'].help_text = "Enter 'Yes' or 'No' for four wheeler zone"
                self.fields['drive_value'].help_text = "Enter 1 if four wheeler, 0 if not"
            elif self.instance.sign_type == 'seatbelt':
                self.fields['sign_value'].help_text = "Enter 'Yes' or 'No' for seatbelt required"
                self.fields['drive_value'].help_text = "Enter 1 if seatbelt worn, 0 if not"

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('rank', 'vehicle_id', 'vehicle_type', 'total_trips', 'total_violations', 'compliance_rate', 'qualification_status', 'last_updated')
    list_filter = ('vehicle__vehicle_type', 'last_updated')
    search_fields = ('vehicle__vehicle_id', 'vehicle__owner_name')
    ordering = ('rank',)
    readonly_fields = ('rank', 'total_violations', 'total_trips', 'compliance_rate', 'average_compliance_score', 'total_tokens_earned', 'last_updated')
    
    def vehicle_id(self, obj):
        return obj.vehicle.vehicle_id
    vehicle_id.short_description = 'Vehicle ID'
    
    def vehicle_type(self, obj):
        return obj.vehicle.get_vehicle_type_display()
    vehicle_type.short_description = 'Vehicle Type'
    
    def compliance_rate(self, obj):
        color = 'green' if obj.compliance_rate >= 90 else 'orange' if obj.compliance_rate >= 70 else 'red'
        return format_html('<span style="color: {};">{}%</span>', color, obj.compliance_rate)
    compliance_rate.short_description = 'Compliance Rate'
    
    def qualification_status(self, obj):
        if obj.total_trips >= 3:
            return format_html('<span style="color: green;">✓ Qualified</span>')
        else:
            return format_html('<span style="color: red;">✗ Needs {} more entries</span>', 3 - obj.total_trips)
    qualification_status.short_description = 'Leaderboard Status'
    
    actions = ['update_rankings']
    
    def update_rankings(self, request, queryset):
        Leaderboard.update_all_rankings()
        self.message_user(request, f"Updated rankings for all vehicles in leaderboard")
    update_rankings.short_description = "Update all leaderboard rankings"

@admin.register(ManualTrafficSign)
class ManualTrafficSignAdmin(admin.ModelAdmin):
    form = ManualTrafficSignForm
    list_display = ('vehicle', 'sign_type', 'sign_value', 'drive_value', 'location', 'created_at', 'is_active')
    list_filter = ('vehicle', 'sign_type', 'is_active', 'created_at')
    search_fields = ('vehicle__vehicle_id', 'vehicle__owner_name', 'sign_type', 'sign_value', 'location')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('vehicle', 'is_active')
        }),
        ('Traffic Sign Details', {
            'fields': ('sign_type', 'location')
        }),
        ('Sign and Drive Values', {
            'fields': ('sign_value', 'drive_value'),
            'description': 'Enter the sign value and actual driving value'
        }),
    )
    
    def get_display_value(self, obj):
        if obj.sign_type == 'speed_limit':
            return f"{obj.sign_value} km/h" if obj.sign_value else "Not set"
        else:
            return obj.sign_value or "Not set"
    get_display_value.short_description = 'Sign Value'

@admin.register(TrafficSign)
class TrafficSignAdmin(admin.ModelAdmin):
    list_display = ('sign_type', 'sign_value', 'detected_at', 'location', 'is_active')
    list_filter = ('sign_type', 'is_active', 'detected_at')
    search_fields = ('sign_type', 'sign_value', 'location')
    ordering = ('-detected_at',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_id', 'vehicle_type', 'registration_number', 'owner_name', 'total_trips', 'total_violations', 'compliance_rate', 'leaderboard_qualified', 'created_at')
    list_filter = ('vehicle_type', 'created_at')
    search_fields = ('vehicle_id', 'registration_number', 'owner_name')
    ordering = ('-created_at',)
    readonly_fields = ('compliance_rate', 'total_violations', 'total_trips', 'average_compliance_score', 'qualifies_for_leaderboard')
    
    def compliance_rate(self, obj):
        color = 'green' if obj.compliance_rate >= 90 else 'orange' if obj.compliance_rate >= 70 else 'red'
        return format_html('<span style="color: {};">{}%</span>', color, obj.compliance_rate)
    compliance_rate.short_description = 'Compliance Rate'
    
    def total_violations(self, obj):
        return obj.total_violations
    total_violations.short_description = 'Violations'
    
    def total_trips(self, obj):
        return obj.total_trips
    total_trips.short_description = 'Trips'
    
    def leaderboard_qualified(self, obj):
        if obj.qualifies_for_leaderboard:
            return format_html('<span style="color: green;">✓ Qualified</span>')
        else:
            remaining = 3 - obj.total_trips
            return format_html('<span style="color: orange;">Needs {} more entries</span>', remaining)
    leaderboard_qualified.short_description = 'Leaderboard Status'

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
