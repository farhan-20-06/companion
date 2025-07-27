from rest_framework import serializers
from .models import TrafficSign, Vehicle, DrivingSession, ComplianceRecord, RewardToken

class TrafficSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSign
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class DrivingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrivingSession
        fields = '__all__'

class ComplianceRecordSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.CharField(source='vehicle.vehicle_id', read_only=True)
    sign_type = serializers.CharField(source='traffic_sign.sign_type', read_only=True)
    sign_value = serializers.CharField(source='traffic_sign.sign_value', read_only=True)
    
    class Meta:
        model = ComplianceRecord
        fields = '__all__'

class RewardTokenSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.CharField(source='vehicle.vehicle_id', read_only=True)
    
    class Meta:
        model = RewardToken
        fields = '__all__'

# API Request/Response Serializers
class SensorDataSerializer(serializers.Serializer):
    """Serializer for incoming sensor data"""
    vehicle_id = serializers.CharField(max_length=50)
    sign_type = serializers.CharField(max_length=20)
    sign_value = serializers.CharField(max_length=50, required=False, allow_blank=True)
    actual_speed = serializers.IntegerField(required=False)
    horn_applied = serializers.BooleanField(required=False, default=False)
    seatbelt_worn = serializers.BooleanField(required=False, default=False)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)

class ComplianceResponseSerializer(serializers.Serializer):
    """Serializer for compliance response"""
    compliance_record_id = serializers.IntegerField()
    violation_type = serializers.CharField()
    severity = serializers.CharField()
    compliance_score = serializers.IntegerField()
    violation_description = serializers.CharField()
    tokens_earned = serializers.IntegerField()