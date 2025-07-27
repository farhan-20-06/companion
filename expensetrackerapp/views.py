from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import TrafficSign, Vehicle, DrivingSession, ComplianceRecord, RewardToken
from .serializers import (
    TrafficSignSerializer, VehicleSerializer, DrivingSessionSerializer,
    ComplianceRecordSerializer, RewardTokenSerializer, SensorDataSerializer,
    ComplianceResponseSerializer
)

@api_view(['POST'])
@permission_classes([AllowAny])
def process_sensor_data(request):
    """
    Process incoming sensor data and create compliance records
    """
    serializer = SensorDataSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Get or create vehicle
        vehicle, created = Vehicle.objects.get_or_create(
            vehicle_id=data['vehicle_id'],
            defaults={
                'vehicle_type': 'four_wheeler',  # Default, can be updated later
                'owner_name': 'Unknown'
            }
        )
        
        # Get or create active driving session
        driving_session, created = DrivingSession.objects.get_or_create(
            vehicle=vehicle,
            is_active=True,
            defaults={'session_start': timezone.now()}
        )
        
        # Create traffic sign record
        traffic_sign = TrafficSign.objects.create(
            sign_type=data['sign_type'],
            sign_value=data.get('sign_value', ''),
            location=data.get('location', ''),
            detected_at=timezone.now()
        )
        
        # Determine seatbelt requirement based on vehicle type
        seatbelt_required = vehicle.vehicle_type == 'four_wheeler'
        
        # Create compliance record
        compliance_record = ComplianceRecord.objects.create(
            driving_session=driving_session,
            traffic_sign=traffic_sign,
            speed_limit=int(data.get('sign_value', 0)) if data.get('sign_value') and data['sign_type'] == 'speed_limit' else None,
            actual_speed=data.get('actual_speed'),
            no_horn_zone=data['sign_type'] == 'no_horn',
            horn_applied=data.get('horn_applied', False),
            seatbelt_required=seatbelt_required,
            seatbelt_worn=data.get('seatbelt_worn', False),
            recorded_at=timezone.now()
        )
        
        # Calculate tokens earned (positive compliance = tokens)
        tokens_earned = 0
        if compliance_record.compliance_score >= 90:
            tokens_earned = 5
        elif compliance_record.compliance_score >= 80:
            tokens_earned = 3
        elif compliance_record.compliance_score >= 70:
            tokens_earned = 1
        
        # Update reward tokens
        reward_token, created = RewardToken.objects.get_or_create(
            vehicle=vehicle,
            defaults={'tokens_earned': tokens_earned}
        )
        if not created:
            reward_token.tokens_earned += tokens_earned
            reward_token.save()
        
        # Prepare response
        response_data = {
            'compliance_record_id': compliance_record.id,
            'violation_type': compliance_record.violation_type,
            'severity': compliance_record.severity,
            'compliance_score': compliance_record.compliance_score,
            'violation_description': compliance_record.violation_description or 'No violations detected',
            'tokens_earned': tokens_earned
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to process sensor data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_vehicle_compliance(request, vehicle_id):
    """
    Get compliance history for a specific vehicle
    """
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        compliance_records = ComplianceRecord.objects.filter(
            driving_session__vehicle=vehicle
        ).order_by('-recorded_at')
        
        serializer = ComplianceRecordSerializer(compliance_records, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get compliance data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_reward_tokens(request, vehicle_id):
    """
    Get reward tokens for a specific vehicle
    """
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        reward_token, created = RewardToken.objects.get_or_create(
            vehicle=vehicle,
            defaults={'tokens_earned': 0, 'tokens_spent': 0}
        )
        
        serializer = RewardTokenSerializer(reward_token)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get reward tokens: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def spend_tokens(request, vehicle_id):
    """
    Spend tokens for rewards
    """
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        reward_token = get_object_or_404(RewardToken, vehicle=vehicle)
        
        tokens_to_spend = request.data.get('tokens', 0)
        if tokens_to_spend > reward_token.tokens_available:
            return Response(
                {'error': 'Insufficient tokens available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reward_token.tokens_spent += tokens_to_spend
        reward_token.save()
        
        serializer = RewardTokenSerializer(reward_token)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to spend tokens: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request, vehicle_id):
    """
    Get dashboard statistics for a vehicle
    """
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        
        # Get recent compliance records
        recent_records = ComplianceRecord.objects.filter(
            driving_session__vehicle=vehicle
        ).order_by('-recorded_at')[:10]
        
        # Calculate statistics
        total_records = ComplianceRecord.objects.filter(
            driving_session__vehicle=vehicle
        ).count()
        
        violations = ComplianceRecord.objects.filter(
            driving_session__vehicle=vehicle,
            violation_type__in=['speed_violation', 'horn_violation', 'seatbelt_violation']
        ).count()
        
        compliance_rate = ((total_records - violations) / total_records * 100) if total_records > 0 else 100
        
        # Get reward tokens
        reward_token, created = RewardToken.objects.get_or_create(
            vehicle=vehicle,
            defaults={'tokens_earned': 0, 'tokens_spent': 0}
        )
        
        stats = {
            'total_trips': total_records,
            'compliance_rate': round(compliance_rate, 2),
            'violations': violations,
            'tokens_available': reward_token.tokens_available,
            'recent_records': ComplianceRecordSerializer(recent_records, many=True).data
        }
        
        return Response(stats)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get dashboard stats: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
