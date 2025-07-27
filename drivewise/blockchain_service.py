import json
import logging
from typing import Dict, List, Optional
from web3 import Web3
from django.conf import settings
from django.core.cache import cache
from .models import Vehicle, ComplianceRecord, Leaderboard, RewardToken

logger = logging.getLogger(__name__)

class BlockchainService:
    def __init__(self):
        self.web3 = None
        self.contract = None
        self.contract_address = None
        self._initialize_web3()
    
    def _initialize_web3(self):
        """Initialize Web3 connection and contract"""
        try:
            # Check if blockchain configuration is properly set
            if (settings.BLOCKCHAIN_CONTRACT_ADDRESS == '0x0000000000000000000000000000000000000000' or 
                settings.BLOCKCHAIN_PRIVATE_KEY == '0x0000000000000000000000000000000000000000000000000000000000000000'):
                logger.warning("Blockchain not properly configured. Using placeholder values.")
                return
            
            # Initialize Web3
            self.web3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_NETWORK_URL))
            
            # Check connection
            if not self.web3.is_connected():
                logger.error("Failed to connect to blockchain network")
                return
            
            # Set contract address
            self.contract_address = settings.BLOCKCHAIN_CONTRACT_ADDRESS
            
            # Load contract ABI (simplified for now)
            self.contract = self._load_contract()
            
            logger.info("Blockchain service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing blockchain service: {e}")
            self.web3 = None
            self.contract = None
    
    def _load_contract(self):
        """Load the smart contract"""
        try:
            # Simplified ABI for testing - in production, load from compiled contract
            contract_abi = [
                {
                    "inputs": [],
                    "stateMutability": "nonpayable",
                    "type": "constructor"
                },
                {
                    "inputs": [
                        {
                            "internalType": "string",
                            "name": "vehicleId",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "vehicleType",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "ownerName",
                            "type": "string"
                        }
                    ],
                    "name": "registerVehicle",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
            
            if self.web3 and self.contract_address:
                return self.web3.eth.contract(
                    address=self.contract_address,
                    abi=contract_abi
                )
            return None
            
        except Exception as e:
            logger.error(f"Error loading contract: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if blockchain is connected and configured"""
        return (self.web3 is not None and 
                self.contract is not None and 
                self.web3.is_connected())
    
    def sync_vehicle_to_blockchain(self, vehicle: Vehicle) -> bool:
        """Sync vehicle data to blockchain"""
        if not self.is_connected():
            logger.warning("Blockchain not connected. Skipping vehicle sync.")
            return False
        
        try:
            # This would call the smart contract to register the vehicle
            # For now, just log the action
            logger.info(f"Would sync vehicle {vehicle.vehicle_id} to blockchain")
            return True
        except Exception as e:
            logger.error(f"Error syncing vehicle to blockchain: {e}")
            return False
    
    def sync_compliance_record_to_blockchain(self, record: ComplianceRecord) -> bool:
        """Sync compliance record to blockchain"""
        if not self.is_connected():
            logger.warning("Blockchain not connected. Skipping compliance record sync.")
            return False
        
        try:
            # This would call the smart contract to add compliance record
            # For now, just log the action
            logger.info(f"Would sync compliance record for vehicle {record.vehicle.vehicle_id} to blockchain")
            return True
        except Exception as e:
            logger.error(f"Error syncing compliance record to blockchain: {e}")
            return False
    
    def get_blockchain_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get leaderboard data from blockchain"""
        if not self.is_connected():
            logger.warning("Blockchain not connected. Returning empty leaderboard.")
            return []
        
        try:
            # This would call the smart contract to get leaderboard
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting blockchain leaderboard: {e}")
            return []
    
    def update_blockchain_leaderboard(self) -> bool:
        """Update leaderboard on blockchain"""
        if not self.is_connected():
            logger.warning("Blockchain not connected. Skipping leaderboard update.")
            return False
        
        try:
            # This would call the smart contract to update leaderboard
            # For now, just log the action
            logger.info("Would update blockchain leaderboard")
            return True
        except Exception as e:
            logger.error(f"Error updating blockchain leaderboard: {e}")
            return False
    
    def sync_all_data_to_blockchain(self) -> Dict[str, int]:
        """Sync all data to blockchain"""
        if not self.is_connected():
            logger.warning("Blockchain not connected. Skipping data sync.")
            return {"vehicles_synced": 0, "records_synced": 0}
        
        try:
            vehicles_synced = 0
            records_synced = 0
            
            # Sync vehicles
            for vehicle in Vehicle.objects.all():
                if self.sync_vehicle_to_blockchain(vehicle):
                    vehicles_synced += 1
            
            # Sync compliance records
            for record in ComplianceRecord.objects.all():
                if self.sync_compliance_record_to_blockchain(record):
                    records_synced += 1
            
            return {
                "vehicles_synced": vehicles_synced,
                "records_synced": records_synced
            }
        except Exception as e:
            logger.error(f"Error syncing all data to blockchain: {e}")
            return {"vehicles_synced": 0, "records_synced": 0}

# Create global instance
blockchain_service = BlockchainService() 