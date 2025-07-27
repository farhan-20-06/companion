from django.urls import path
from . import views

urlpatterns = [
    # Sensor data processing
    path('sensor-data/', views.process_sensor_data, name='process_sensor_data'),
    
    # Vehicle compliance and statistics
    path('vehicle/<str:vehicle_id>/compliance/', views.get_vehicle_compliance, name='get_vehicle_compliance'),
    path('vehicle/<str:vehicle_id>/tokens/', views.get_reward_tokens, name='get_reward_tokens'),
    path('vehicle/<str:vehicle_id>/spend-tokens/', views.spend_tokens, name='spend_tokens'),
    path('vehicle/<str:vehicle_id>/dashboard/', views.get_dashboard_stats, name='get_dashboard_stats'),
] 