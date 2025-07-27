from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import TrafficSign, Vehicle, ComplianceRecord, RewardToken, Leaderboard
from .serializers import (
    TrafficSignSerializer, VehicleSerializer, ComplianceRecordSerializer,
    RewardTokenSerializer, SensorDataSerializer, ComplianceResponseSerializer
)
from .blockchain_service import blockchain_service

@api_view(['POST'])
@permission_classes([AllowAny])
def process_sensor_data(request):
    """
    Process sensor data and create compliance records
    """
    try:
        serializer = SensorDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        vehicle_id = data['vehicle_id']
        
        # Get or create vehicle
        vehicle, created = Vehicle.objects.get_or_create(
            vehicle_id=vehicle_id,
            defaults={
                'vehicle_type': 'four_wheeler',  # Default type
                'owner_name': 'Unknown'
            }
        )
        
        # Create traffic sign
        traffic_sign = TrafficSign.objects.create(
            sign_type=data['sign_type'],
            sign_value=data.get('sign_value', ''),
            location=data.get('location', '')
        )
        
        # Create compliance record
        compliance_record = ComplianceRecord.objects.create(
            vehicle=vehicle,
            traffic_sign=traffic_sign,
            speed_limit=int(data.get('drive_value', 0)) if data['sign_type'] == 'speed_limit' else None,
            actual_speed=int(data.get('drive_value', 0)) if data['sign_type'] == 'speed_limit' else None,
            no_horn_zone=data['sign_type'] == 'no_horn',
            horn_applied=data.get('drive_value', 0) == 1 if data['sign_type'] == 'no_horn' else False,
            seatbelt_required=vehicle.vehicle_type == 'four_wheeler',
            seatbelt_worn=data.get('drive_value', 0) == 1 if data['sign_type'] == 'seatbelt' else False
        )
        
        # Calculate compliance score and violation
        compliance_score = compliance_record.calculate_compliance_score()
        violation_type = compliance_record.violation_type
        
        # Award tokens based on compliance
        tokens_earned = 0
        if compliance_score >= 90:
            tokens_earned = 10
        elif compliance_score >= 70:
            tokens_earned = 5
        elif compliance_score >= 50:
            tokens_earned = 2
        
        # Update or create reward token
        reward_token, created = RewardToken.objects.get_or_create(
            vehicle=vehicle,
            defaults={'tokens_earned': tokens_earned}
        )
        if not created:
            reward_token.tokens_earned += tokens_earned
            reward_token.save()
        
        # Sync to blockchain if connected
        if blockchain_service.is_connected():
            try:
                blockchain_service.sync_vehicle_to_blockchain(vehicle)
                blockchain_service.sync_compliance_record_to_blockchain(compliance_record)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Blockchain sync error: {e}")
        
        # Update leaderboard
        Leaderboard.update_all_rankings()
        
        # Get current rank
        current_rank = None
        try:
            leaderboard_entry = Leaderboard.objects.get(vehicle=vehicle)
            current_rank = leaderboard_entry.rank
        except Leaderboard.DoesNotExist:
            pass
        
        response_data = {
            'status': 'success',
            'message': 'Sensor data processed successfully',
            'violation_detected': violation_type != 'no_violation',
            'violation_type': violation_type if violation_type != 'no_violation' else None,
            'compliance_score': compliance_score,
            'violation_description': compliance_record.violation_description,
            'tokens_earned': tokens_earned,
            'total_trips': vehicle.total_trips,
            'qualification_status': 'Qualified' if vehicle.total_trips >= 3 else f'Needs {3 - vehicle.total_trips} more entries',
            'current_rank': current_rank
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
    Get compliance records for a specific vehicle
    """
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        records = ComplianceRecord.objects.filter(vehicle=vehicle).order_by('-recorded_at')
        
        serializer = ComplianceRecordSerializer(records, many=True)
        
        return Response({
            'vehicle_id': vehicle_id,
            'total_records': records.count(),
            'compliance_rate': vehicle.compliance_rate,
            'total_violations': vehicle.total_violations,
            'records': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get vehicle compliance: {str(e)}'},
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
        
        amount = request.data.get('amount', 0)
        reward_type = request.data.get('reward_type', 'unknown')
        
        if reward_token.tokens_available < amount:
            return Response(
                {'error': 'Insufficient tokens'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reward_token.tokens_spent += amount
        reward_token.save()
        
        # Sync to blockchain if connected
        if blockchain_service.is_connected():
            try:
                blockchain_service.claim_reward(vehicle_id, reward_type, amount)
            except Exception as e:
                print(f"Blockchain reward claim error: {e}")
        
        return Response({
            'status': 'success',
            'message': f'Successfully spent {amount} tokens for {reward_type}',
            'tokens_available': reward_token.tokens_available
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to spend tokens: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request, vehicle_id):
    """
    Get dashboard statistics for a specific vehicle
    """
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        
        # Get leaderboard entry
        current_rank = None
        qualification_status = 'Not Qualified'
        if vehicle.qualifies_for_leaderboard:
            try:
                leaderboard_entry = Leaderboard.objects.get(vehicle=vehicle)
                current_rank = leaderboard_entry.rank
                qualification_status = 'Qualified'
            except Leaderboard.DoesNotExist:
                qualification_status = 'Qualified (Not Ranked)'
        
        return Response({
            'vehicle_id': vehicle_id,
            'total_trips': vehicle.total_trips,
            'total_violations': vehicle.total_violations,
            'compliance_rate': vehicle.compliance_rate,
            'average_compliance_score': vehicle.average_compliance_score,
            'qualification_status': qualification_status,
            'current_rank': current_rank,
            'tokens_earned': getattr(vehicle.rewardtoken, 'tokens_earned', 0),
            'tokens_available': getattr(vehicle.rewardtoken, 'tokens_available', 0)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get dashboard stats: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_leaderboard(request):
    """
    Get leaderboard rankings for all vehicles (minimum 3 entries required)
    """
    try:
        # Update rankings first
        Leaderboard.update_all_rankings()
        
        # Get top vehicles (limit to top 10 by default)
        limit = request.GET.get('limit', 10)
        leaderboard_entries = Leaderboard.objects.all().order_by('rank')[:int(limit)]
        
        leaderboard_data = []
        for entry in leaderboard_entries:
            leaderboard_data.append({
                'rank': entry.rank,
                'vehicle_id': entry.vehicle.vehicle_id,
                'vehicle_type': entry.vehicle.get_vehicle_type_display(),
                'owner_name': entry.vehicle.owner_name or 'Unknown',
                'total_trips': entry.total_trips,
                'total_violations': entry.total_violations,
                'compliance_rate': float(entry.compliance_rate),
                'average_compliance_score': float(entry.average_compliance_score),
                'total_tokens_earned': entry.total_tokens_earned,
                'qualification_status': 'Qualified' if entry.total_trips >= 3 else f'Needs {3 - entry.total_trips} more entries',
                'last_updated': entry.last_updated.isoformat()
            })
        
        # Get qualification statistics
        total_vehicles = Vehicle.objects.annotate(
            trip_count=Count('compliancerecord')
        ).filter(trip_count__gte=3).count()
        
        # Try to get blockchain data if available
        blockchain_data = []
        if blockchain_service.is_connected():
            try:
                blockchain_data = blockchain_service.get_blockchain_leaderboard(int(limit))
            except Exception as e:
                print(f"Blockchain leaderboard error: {e}")
        
        return Response({
            'leaderboard': leaderboard_data,
            'blockchain_leaderboard': blockchain_data,
            'total_qualified_vehicles': total_vehicles,
            'minimum_entries_required': 3,
            'ranking_criteria': [
                '1. Maximum number of entries (highest first)',
                '2. Minimum violations (lowest first)',
                '3. Compliance rate (highest first)'
            ],
            'blockchain_connected': blockchain_service.is_connected(),
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get leaderboard: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_vehicle_ranking(request, vehicle_id):
    """
    Get ranking for a specific vehicle
    """
    try:
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        
        if not vehicle.qualifies_for_leaderboard:
            return Response({
                'error': f'Vehicle {vehicle_id} does not meet minimum requirements (3 entries needed)',
                'total_trips': vehicle.total_trips,
                'needed_entries': 3 - vehicle.total_trips
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            leaderboard_entry = Leaderboard.objects.get(vehicle=vehicle)
            return Response({
                'vehicle_id': vehicle_id,
                'rank': leaderboard_entry.rank,
                'total_trips': leaderboard_entry.total_trips,
                'total_violations': leaderboard_entry.total_violations,
                'compliance_rate': float(leaderboard_entry.compliance_rate),
                'average_compliance_score': float(leaderboard_entry.average_compliance_score),
                'total_tokens_earned': leaderboard_entry.total_tokens_earned
            })
        except Leaderboard.DoesNotExist:
            return Response({
                'error': f'Vehicle {vehicle_id} is qualified but not ranked yet'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get vehicle ranking: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def sync_to_blockchain(request):
    """
    Sync all data to blockchain
    """
    try:
        if not blockchain_service.is_connected():
            return Response({
                'error': 'Blockchain not connected',
                'blockchain_status': 'disconnected'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        sync_results = blockchain_service.sync_all_data_to_blockchain()
        
        return Response({
            'status': 'success',
            'message': 'Data synced to blockchain',
            'blockchain_status': 'connected',
            'sync_results': sync_results
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to sync to blockchain: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def update_blockchain_leaderboard(request):
    """
    Update leaderboard rankings on blockchain
    """
    try:
        if not blockchain_service.is_connected():
            return Response({
                'error': 'Blockchain not connected',
                'blockchain_status': 'disconnected'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        success = blockchain_service.update_blockchain_leaderboard()
        
        if success:
            return Response({
                'status': 'success',
                'message': 'Blockchain leaderboard updated',
                'blockchain_status': 'connected'
            })
        else:
            return Response({
                'error': 'Failed to update blockchain leaderboard',
                'blockchain_status': 'connected'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to update blockchain leaderboard: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
