# DriveWise Blockchain Integration

This directory contains the blockchain integration for the DriveWise leaderboard system using Solidity smart contracts.

## Overview

The DriveWise blockchain integration provides:
- **Decentralized Leaderboard**: Vehicle rankings stored on the blockchain
- **Immutable Compliance Records**: All driving compliance data stored securely
- **Token Rewards System**: Earn tokens for good driving behavior
- **Smart Contract Automation**: Automatic ranking calculations and token distribution

## Smart Contract Features

### DriveWiseLeaderboard.sol

The main smart contract that handles:

1. **Vehicle Registration**
   - Register vehicles with unique IDs
   - Store vehicle type and owner information
   - Track vehicle status

2. **Compliance Record Management**
   - Store speed limit violations
   - Track horn usage in no-horn zones
   - Monitor seatbelt compliance
   - Calculate compliance scores automatically

3. **Leaderboard System**
   - Rank vehicles based on multiple criteria:
     - Maximum number of trips (descending)
     - Minimum violations (ascending)
     - Compliance rate (descending)
   - Minimum 3 entries required for leaderboard qualification

4. **Token Rewards**
   - Award tokens based on compliance scores:
     - 90-100%: 10 tokens (Excellent)
     - 70-89%: 5 tokens (Good)
     - 50-69%: 2 tokens (Average)
     - Below 50%: 0 tokens (Poor)
   - Claim rewards for real-world items (petrol, diesel, tyres)

5. **Security Features**
   - Access control with Ownable pattern
   - Reentrancy protection
   - Input validation and error handling

## Setup Instructions

### Prerequisites

1. **Node.js and npm** (v16 or higher)
2. **Hardhat** (for smart contract development)
3. **Python** (for Django integration)
4. **Web3.py** (for Python blockchain interaction)

### Installation

1. **Install blockchain dependencies**:
   ```bash
   cd blockchain
   npm install
   ```

2. **Install Python dependencies**:
   ```bash
   pip install web3
   ```

3. **Configure environment variables**:
   Create a `.env` file in the blockchain directory:
   ```
   BLOCKCHAIN_CONTRACT_ADDRESS=your_contract_address
   BLOCKCHAIN_PRIVATE_KEY=your_private_key
   BLOCKCHAIN_NETWORK_URL=http://127.0.0.1:8545
   ```

### Compilation and Deployment

1. **Compile smart contracts**:
   ```bash
   cd blockchain
   npm run compile
   ```

2. **Deploy to local network**:
   ```bash
   # Start local Hardhat node
   npm run node
   
   # In another terminal, deploy contracts
   npm run deploy:local
   ```

3. **Deploy to testnet/mainnet**:
   ```bash
   npm run deploy
   ```

## Django Integration

### Configuration

Add blockchain settings to your Django settings:

```python
# Blockchain Configuration
BLOCKCHAIN_CONTRACT_ADDRESS = 'your_contract_address'
BLOCKCHAIN_PRIVATE_KEY = 'your_private_key'
BLOCKCHAIN_NETWORK_URL = 'http://127.0.0.1:8545'  # or your network URL
```

### API Endpoints

The blockchain integration adds these new endpoints:

1. **Sync Data to Blockchain**:
   ```
   POST /api/blockchain/sync/
   ```

2. **Update Blockchain Leaderboard**:
   ```
   POST /api/blockchain/leaderboard/update/
   ```

3. **Enhanced Leaderboard** (includes blockchain data):
   ```
   GET /api/leaderboard/
   ```

### Management Commands

Use Django management commands to interact with the blockchain:

```bash
# Sync all data to blockchain
python manage.py sync_blockchain

# Sync only vehicles
python manage.py sync_blockchain --vehicles-only

# Sync only compliance records
python manage.py sync_blockchain --records-only

# Update leaderboard rankings
python manage.py sync_blockchain --update-leaderboard
```

## Smart Contract Functions

### Core Functions

1. **registerVehicle(vehicleId, vehicleType, ownerName)**
   - Register a new vehicle on the blockchain
   - Only callable by contract owner

2. **addComplianceRecord(vehicleId, speedLimit, actualSpeed, noHornZone, hornApplied, seatbeltRequired, seatbeltWorn)**
   - Add a compliance record for a vehicle
   - Automatically calculates violations and compliance score
   - Awards tokens based on performance

3. **updateLeaderboard()**
   - Update all vehicle rankings
   - Sorts by trips, violations, and compliance rate

4. **claimReward(vehicleId, rewardType, cost)**
   - Spend tokens for real-world rewards
   - Prevents overspending

### View Functions

1. **getVehicle(vehicleId)**
   - Get complete vehicle information

2. **getLeaderboard(limit)**
   - Get ranked leaderboard data

3. **getComplianceRecords(vehicleId)**
   - Get all compliance records for a vehicle

4. **getRewardToken(vehicleId)**
   - Get token balance and spending history

## Events

The smart contract emits events for important actions:

- `VehicleRegistered(vehicleId, vehicleType, ownerName)`
- `ComplianceRecordAdded(vehicleId, complianceScore, violationType)`
- `TokensEarned(vehicleId, amount)`
- `TokensSpent(vehicleId, amount)`
- `LeaderboardUpdated(vehicleId, newRank)`
- `RewardClaimed(vehicleId, rewardType, cost)`

## Security Considerations

1. **Access Control**: Only contract owner can register vehicles and update leaderboard
2. **Input Validation**: All inputs are validated before processing
3. **Reentrancy Protection**: Prevents reentrancy attacks
4. **Gas Optimization**: Contract is optimized for gas efficiency
5. **Error Handling**: Comprehensive error messages and handling

## Testing

### Smart Contract Tests

```bash
cd blockchain
npm test
```

### Integration Tests

```bash
# Test Django blockchain integration
python manage.py test drivewise.tests.test_blockchain
```

## Deployment

### Local Development

1. Start Hardhat node:
   ```bash
   npm run node
   ```

2. Deploy contracts:
   ```bash
   npm run deploy:local
   ```

3. Update Django settings with contract address

### Production Deployment

1. Deploy to mainnet:
   ```bash
   npm run deploy
   ```

2. Verify contract on Etherscan:
   ```bash
   npm run verify
   ```

3. Update production Django settings

## Troubleshooting

### Common Issues

1. **Blockchain Connection Failed**
   - Check network URL in settings
   - Ensure Hardhat node is running
   - Verify private key is correct

2. **Gas Limit Exceeded**
   - Increase gas limit in transaction
   - Optimize contract functions
   - Use gas estimation

3. **Contract Not Found**
   - Verify contract address in settings
   - Check if contract is deployed
   - Ensure correct network

### Debug Commands

```bash
# Check blockchain connection
python manage.py shell -c "from drivewise.blockchain_service import blockchain_service; print(blockchain_service.is_connected())"

# Test contract interaction
python manage.py shell -c "from drivewise.blockchain_service import blockchain_service; print(blockchain_service.get_blockchain_leaderboard(5))"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 