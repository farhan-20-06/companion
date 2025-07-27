// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DriveWiseLeaderboard
 * @dev Smart contract for managing DriveWise leaderboard and rewards system
 */
contract DriveWiseLeaderboard {
    // Structs
    struct Vehicle {
        string vehicleId;
        string vehicleType;
        string ownerName;
        uint256 totalTrips;
        uint256 totalViolations;
        uint256 complianceRate;
        uint256 averageComplianceScore;
        uint256 tokensEarned;
        uint256 rank;
        bool isActive;
        uint256 lastUpdated;
    }
    
    struct ComplianceRecord {
        string vehicleId;
        uint256 speedLimit;
        uint256 actualSpeed;
        bool noHornZone;
        bool hornApplied;
        bool seatbeltRequired;
        bool seatbeltWorn;
        string violationType;
        uint256 complianceScore;
        uint256 timestamp;
    }
    
    struct RewardToken {
        string vehicleId;
        uint256 tokensEarned;
        uint256 tokensSpent;
        uint256 lastUpdated;
    }
    
    // State variables
    mapping(string => Vehicle) public vehicles;
    mapping(string => ComplianceRecord[]) public complianceRecords;
    mapping(string => RewardToken) public rewardTokens;
    mapping(uint256 => string) public rankToVehicle;
    mapping(string => uint256) public vehicleToRank;
    
    uint256 private _vehicleCount;
    uint256 private _complianceRecordCount;
    
    address public owner;
    
    // Events
    event VehicleRegistered(string vehicleId, string vehicleType, string ownerName);
    event ComplianceRecordAdded(string vehicleId, uint256 complianceScore, string violationType);
    event TokensEarned(string vehicleId, uint256 amount);
    event TokensSpent(string vehicleId, uint256 amount);
    event LeaderboardUpdated(string vehicleId, uint256 newRank);
    event RewardClaimed(string vehicleId, string rewardType, uint256 cost);
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier onlyRegisteredVehicle(string memory vehicleId) {
        require(vehicles[vehicleId].isActive, "Vehicle not registered");
        _;
    }
    
    modifier minimumTripsRequired(string memory vehicleId) {
        require(vehicles[vehicleId].totalTrips >= 3, "Minimum 3 trips required for leaderboard");
        _;
    }
    
    // Constructor
    constructor() {
        owner = msg.sender;
        _vehicleCount = 0;
    }
    
    /**
     * @dev Register a new vehicle
     * @param vehicleId Unique vehicle identifier
     * @param vehicleType Type of vehicle (two_wheeler, four_wheeler, commercial)
     * @param ownerName Name of the vehicle owner
     */
    function registerVehicle(
        string memory vehicleId,
        string memory vehicleType,
        string memory ownerName
    ) external onlyOwner {
        require(!vehicles[vehicleId].isActive, "Vehicle already registered");
        
        vehicles[vehicleId] = Vehicle({
            vehicleId: vehicleId,
            vehicleType: vehicleType,
            ownerName: ownerName,
            totalTrips: 0,
            totalViolations: 0,
            complianceRate: 100,
            averageComplianceScore: 100,
            tokensEarned: 0,
            rank: 0,
            isActive: true,
            lastUpdated: block.timestamp
        });
        
        // Initialize reward token record
        rewardTokens[vehicleId] = RewardToken({
            vehicleId: vehicleId,
            tokensEarned: 0,
            tokensSpent: 0,
            lastUpdated: block.timestamp
        });
        
        _vehicleCount++;
        
        emit VehicleRegistered(vehicleId, vehicleType, ownerName);
    }
    
    /**
     * @dev Add a compliance record for a vehicle
     * @param vehicleId Vehicle identifier
     * @param speedLimit Speed limit from traffic sign
     * @param actualSpeed Actual speed of vehicle
     * @param noHornZone Whether it's a no-horn zone
     * @param hornApplied Whether horn was applied
     * @param seatbeltRequired Whether seatbelt is required
     * @param seatbeltWorn Whether seatbelt was worn
     */
    function addComplianceRecord(
        string memory vehicleId,
        uint256 speedLimit,
        uint256 actualSpeed,
        bool noHornZone,
        bool hornApplied,
        bool seatbeltRequired,
        bool seatbeltWorn
    ) external onlyOwner onlyRegisteredVehicle(vehicleId) {
        // Calculate violation type and compliance score
        string memory violationType = "no_violation";
        uint256 complianceScore = 100;
        
        // Speed violation check
        if (speedLimit > 0 && actualSpeed > speedLimit) {
            violationType = "speed_violation";
            complianceScore -= 20;
            if (actualSpeed > speedLimit + 20) {
                complianceScore -= 10; // Additional penalty for excessive speed
            }
        }
        
        // Horn violation check
        if (noHornZone && hornApplied) {
            violationType = "horn_violation";
            complianceScore -= 15;
        }
        
        // Seatbelt violation check
        if (seatbeltRequired && !seatbeltWorn) {
            violationType = "seatbelt_violation";
            complianceScore -= 25;
        }
        
        // Ensure compliance score doesn't go below 0
        if (complianceScore < 0) {
            complianceScore = 0;
        }
        
        // Create compliance record
        ComplianceRecord memory record = ComplianceRecord({
            vehicleId: vehicleId,
            speedLimit: speedLimit,
            actualSpeed: actualSpeed,
            noHornZone: noHornZone,
            hornApplied: hornApplied,
            seatbeltRequired: seatbeltRequired,
            seatbeltWorn: seatbeltWorn,
            violationType: violationType,
            complianceScore: complianceScore,
            timestamp: block.timestamp
        });
        
        // Add to compliance records
        complianceRecords[vehicleId].push(record);
        _complianceRecordCount++;
        
        // Update vehicle statistics
        _updateVehicleStats(vehicleId);
        
        // Award tokens based on compliance
        uint256 tokensToAward = _calculateTokens(complianceScore);
        if (tokensToAward > 0) {
            _awardTokens(vehicleId, tokensToAward);
        }
        
        emit ComplianceRecordAdded(vehicleId, complianceScore, violationType);
    }
    
    /**
     * @dev Update vehicle statistics
     * @param vehicleId Vehicle identifier
     */
    function _updateVehicleStats(string memory vehicleId) internal {
        Vehicle storage vehicle = vehicles[vehicleId];
        ComplianceRecord[] storage records = complianceRecords[vehicleId];
        
        vehicle.totalTrips = records.length;
        
        // Calculate violations
        uint256 violations = 0;
        uint256 totalScore = 0;
        
        for (uint256 i = 0; i < records.length; i++) {
            if (keccak256(bytes(records[i].violationType)) != keccak256(bytes("no_violation"))) {
                violations++;
            }
            totalScore += records[i].complianceScore;
        }
        
        vehicle.totalViolations = violations;
        
        // Calculate compliance rate
        if (vehicle.totalTrips > 0) {
            vehicle.complianceRate = ((vehicle.totalTrips - violations) * 100) / vehicle.totalTrips;
            vehicle.averageComplianceScore = totalScore / vehicle.totalTrips;
        }
        
        vehicle.lastUpdated = block.timestamp;
    }
    
    /**
     * @dev Calculate tokens to award based on compliance score
     * @param complianceScore The compliance score (0-100)
     * @return tokensToAward Number of tokens to award
     */
    function _calculateTokens(uint256 complianceScore) internal pure returns (uint256) {
        if (complianceScore >= 90) {
            return 10; // Excellent driving
        } else if (complianceScore >= 70) {
            return 5;  // Good driving
        } else if (complianceScore >= 50) {
            return 2;  // Average driving
        } else {
            return 0;  // Poor driving - no tokens
        }
    }
    
    /**
     * @dev Award tokens to a vehicle
     * @param vehicleId Vehicle identifier
     * @param amount Amount of tokens to award
     */
    function _awardTokens(string memory vehicleId, uint256 amount) internal {
        RewardToken storage token = rewardTokens[vehicleId];
        token.tokensEarned += amount;
        token.lastUpdated = block.timestamp;
        
        vehicles[vehicleId].tokensEarned = token.tokensEarned;
        
        emit TokensEarned(vehicleId, amount);
    }
    
    /**
     * @dev Update leaderboard rankings
     */
    function updateLeaderboard() external onlyOwner {
        // Clear existing rankings
        for (uint256 i = 1; i <= _vehicleCount; i++) {
            if (bytes(rankToVehicle[i]).length > 0) {
                delete vehicleToRank[rankToVehicle[i]];
                delete rankToVehicle[i];
            }
        }
        
        // Create a temporary array for sorting
        string[] memory qualifiedVehicles = new string[](_vehicleCount);
        uint256 qualifiedCount = 0;
        
        // Find qualified vehicles (minimum 3 trips)
        for (uint256 i = 1; i <= _vehicleCount; i++) {
            string memory vehicleId = rankToVehicle[i];
            if (vehicles[vehicleId].isActive && vehicles[vehicleId].totalTrips >= 3) {
                qualifiedVehicles[qualifiedCount] = vehicleId;
                qualifiedCount++;
            }
        }
        
        // Sort vehicles by criteria:
        // 1. Maximum trips (descending)
        // 2. Minimum violations (ascending)
        // 3. Compliance rate (descending)
        for (uint256 i = 0; i < qualifiedCount - 1; i++) {
            for (uint256 j = i + 1; j < qualifiedCount; j++) {
                if (_shouldSwap(qualifiedVehicles[i], qualifiedVehicles[j])) {
                    string memory temp = qualifiedVehicles[i];
                    qualifiedVehicles[i] = qualifiedVehicles[j];
                    qualifiedVehicles[j] = temp;
                }
            }
        }
        
        // Assign ranks
        for (uint256 i = 0; i < qualifiedCount; i++) {
            uint256 rank = i + 1;
            string memory vehicleId = qualifiedVehicles[i];
            
            vehicles[vehicleId].rank = rank;
            rankToVehicle[rank] = vehicleId;
            vehicleToRank[vehicleId] = rank;
            
            emit LeaderboardUpdated(vehicleId, rank);
        }
    }
    
    /**
     * @dev Determine if two vehicles should be swapped in ranking
     * @param vehicle1 First vehicle ID
     * @param vehicle2 Second vehicle ID
     * @return True if vehicles should be swapped
     */
    function _shouldSwap(string memory vehicle1, string memory vehicle2) internal view returns (bool) {
        Vehicle memory v1 = vehicles[vehicle1];
        Vehicle memory v2 = vehicles[vehicle2];
        
        // Primary: More trips
        if (v1.totalTrips != v2.totalTrips) {
            return v1.totalTrips < v2.totalTrips;
        }
        
        // Secondary: Fewer violations
        if (v1.totalViolations != v2.totalViolations) {
            return v1.totalViolations > v2.totalViolations;
        }
        
        // Tertiary: Higher compliance rate
        return v1.complianceRate < v2.complianceRate;
    }
    
    /**
     * @dev Claim reward tokens for real-world items
     * @param vehicleId Vehicle identifier
     * @param rewardType Type of reward (petrol, diesel, tyres)
     * @param cost Cost in tokens
     */
    function claimReward(
        string memory vehicleId,
        string memory rewardType,
        uint256 cost
    ) external onlyOwner onlyRegisteredVehicle(vehicleId) {
        RewardToken storage token = rewardTokens[vehicleId];
        require(token.tokensEarned - token.tokensSpent >= cost, "Insufficient tokens");
        
        token.tokensSpent += cost;
        token.lastUpdated = block.timestamp;
        
        emit RewardClaimed(vehicleId, rewardType, cost);
    }
    
    // View functions
    function getVehicle(string memory vehicleId) external view returns (Vehicle memory) {
        return vehicles[vehicleId];
    }
    
    function getComplianceRecords(string memory vehicleId) external view returns (ComplianceRecord[] memory) {
        return complianceRecords[vehicleId];
    }
    
    function getRewardToken(string memory vehicleId) external view returns (RewardToken memory) {
        return rewardTokens[vehicleId];
    }
    
    function getLeaderboard(uint256 limit) external view returns (string[] memory) {
        uint256 actualLimit = limit > _vehicleCount ? _vehicleCount : limit;
        string[] memory leaderboard = new string[](actualLimit);
        
        for (uint256 i = 1; i <= actualLimit; i++) {
            leaderboard[i - 1] = rankToVehicle[i];
        }
        
        return leaderboard;
    }
    
    function getVehicleRank(string memory vehicleId) external view returns (uint256) {
        return vehicleToRank[vehicleId];
    }
    
    function getTotalVehicles() external view returns (uint256) {
        return _vehicleCount;
    }
    
    function getTotalComplianceRecords() external view returns (uint256) {
        return _complianceRecordCount;
    }
} 