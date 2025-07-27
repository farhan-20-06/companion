const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DriveWiseLeaderboard", function () {
  let driveWiseLeaderboard;
  let owner;
  let addr1;
  let addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    
    const DriveWiseLeaderboard = await ethers.getContractFactory("DriveWiseLeaderboard");
    driveWiseLeaderboard = await DriveWiseLeaderboard.deploy();
    await driveWiseLeaderboard.waitForDeployment();
  });

  describe("Vehicle Registration", function () {
    it("Should register a vehicle successfully", async function () {
      await driveWiseLeaderboard.registerVehicle("VEH001", "four_wheeler", "John Doe");
      
      const vehicle = await driveWiseLeaderboard.getVehicle("VEH001");
      expect(vehicle.vehicleId).to.equal("VEH001");
      expect(vehicle.vehicleType).to.equal("four_wheeler");
      expect(vehicle.ownerName).to.equal("John Doe");
      expect(vehicle.isActive).to.be.true;
    });

    it("Should not allow duplicate vehicle registration", async function () {
      await driveWiseLeaderboard.registerVehicle("VEH001", "four_wheeler", "John Doe");
      
      await expect(
        driveWiseLeaderboard.registerVehicle("VEH001", "two_wheeler", "Jane Doe")
      ).to.be.revertedWith("Vehicle already registered");
    });

    it("Should only allow owner to register vehicles", async function () {
      await expect(
        driveWiseLeaderboard.connect(addr1).registerVehicle("VEH001", "four_wheeler", "John Doe")
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Compliance Records", function () {
    beforeEach(async function () {
      await driveWiseLeaderboard.registerVehicle("VEH001", "four_wheeler", "John Doe");
    });

    it("Should add compliance record for speed violation", async function () {
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001",
        40,  // speed limit
        60,  // actual speed (violation)
        false, // no horn zone
        false, // horn applied
        true,  // seatbelt required
        true   // seatbelt worn
      );

      const vehicle = await driveWiseLeaderboard.getVehicle("VEH001");
      expect(vehicle.totalTrips).to.equal(1);
      expect(vehicle.totalViolations).to.equal(1);
      expect(vehicle.complianceRate).to.equal(0); // 0% compliance due to violation
    });

    it("Should add compliance record for horn violation", async function () {
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001",
        0,   // speed limit (not applicable)
        0,   // actual speed
        true, // no horn zone
        true, // horn applied (violation)
        true, // seatbelt required
        true  // seatbelt worn
      );

      const vehicle = await driveWiseLeaderboard.getVehicle("VEH001");
      expect(vehicle.totalTrips).to.equal(1);
      expect(vehicle.totalViolations).to.equal(1);
    });

    it("Should add compliance record for seatbelt violation", async function () {
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001",
        0,    // speed limit
        0,    // actual speed
        false, // no horn zone
        false, // horn applied
        true,  // seatbelt required
        false  // seatbelt worn (violation)
      );

      const vehicle = await driveWiseLeaderboard.getVehicle("VEH001");
      expect(vehicle.totalTrips).to.equal(1);
      expect(vehicle.totalViolations).to.equal(1);
    });

    it("Should award tokens for good compliance", async function () {
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001",
        40,  // speed limit
        35,  // actual speed (good compliance)
        false, // no horn zone
        false, // horn applied
        true,  // seatbelt required
        true   // seatbelt worn
      );

      const rewardToken = await driveWiseLeaderboard.getRewardToken("VEH001");
      expect(rewardToken.tokensEarned).to.be.greaterThan(0);
    });

    it("Should not allow compliance record for unregistered vehicle", async function () {
      await expect(
        driveWiseLeaderboard.addComplianceRecord(
          "UNREGISTERED",
          40, 0, false, false, true, true
        )
      ).to.be.revertedWith("Vehicle not registered");
    });
  });

  describe("Leaderboard Rankings", function () {
    beforeEach(async function () {
      // Register multiple vehicles
      await driveWiseLeaderboard.registerVehicle("VEH001", "four_wheeler", "John Doe");
      await driveWiseLeaderboard.registerVehicle("VEH002", "two_wheeler", "Jane Doe");
      await driveWiseLeaderboard.registerVehicle("VEH003", "commercial", "Bob Smith");
    });

    it("Should update leaderboard rankings", async function () {
      // Add compliance records to qualify vehicles
      for (let i = 0; i < 3; i++) {
        await driveWiseLeaderboard.addComplianceRecord(
          "VEH001", 40, 35, false, false, true, true
        );
        await driveWiseLeaderboard.addComplianceRecord(
          "VEH002", 40, 35, false, false, false, true
        );
        await driveWiseLeaderboard.addComplianceRecord(
          "VEH003", 40, 35, false, false, true, true
        );
      }

      await driveWiseLeaderboard.updateLeaderboard();

      const leaderboard = await driveWiseLeaderboard.getLeaderboard(10);
      expect(leaderboard.length).to.be.greaterThan(0);
    });

    it("Should require minimum 3 trips for leaderboard qualification", async function () {
      // Add only 2 compliance records (not enough for qualification)
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001", 40, 35, false, false, true, true
      );
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001", 40, 35, false, false, true, true
      );

      await driveWiseLeaderboard.updateLeaderboard();

      const leaderboard = await driveWiseLeaderboard.getLeaderboard(10);
      // Vehicle should not be in leaderboard due to insufficient trips
      expect(leaderboard.filter(id => id === "VEH001").length).to.equal(0);
    });
  });

  describe("Token Rewards", function () {
    beforeEach(async function () {
      await driveWiseLeaderboard.registerVehicle("VEH001", "four_wheeler", "John Doe");
    });

    it("Should award tokens based on compliance score", async function () {
      // Excellent compliance (90-100%)
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001", 40, 35, false, false, true, true
      );

      const rewardToken = await driveWiseLeaderboard.getRewardToken("VEH001");
      expect(rewardToken.tokensEarned).to.equal(10); // Excellent driving
    });

    it("Should allow claiming rewards", async function () {
      // Earn tokens first
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001", 40, 35, false, false, true, true
      );

      // Claim reward
      await driveWiseLeaderboard.claimReward("VEH001", "petrol", 5);

      const rewardToken = await driveWiseLeaderboard.getRewardToken("VEH001");
      expect(rewardToken.tokensSpent).to.equal(5);
    });

    it("Should prevent overspending tokens", async function () {
      // Earn tokens first
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001", 40, 35, false, false, true, true
      );

      // Try to spend more tokens than available
      await expect(
        driveWiseLeaderboard.claimReward("VEH001", "petrol", 20)
      ).to.be.revertedWith("Insufficient tokens");
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await driveWiseLeaderboard.registerVehicle("VEH001", "four_wheeler", "John Doe");
    });

    it("Should return vehicle information", async function () {
      const vehicle = await driveWiseLeaderboard.getVehicle("VEH001");
      expect(vehicle.vehicleId).to.equal("VEH001");
      expect(vehicle.vehicleType).to.equal("four_wheeler");
      expect(vehicle.ownerName).to.equal("John Doe");
    });

    it("Should return compliance records", async function () {
      await driveWiseLeaderboard.addComplianceRecord(
        "VEH001", 40, 35, false, false, true, true
      );

      const records = await driveWiseLeaderboard.getComplianceRecords("VEH001");
      expect(records.length).to.equal(1);
    });

    it("Should return reward token information", async function () {
      const rewardToken = await driveWiseLeaderboard.getRewardToken("VEH001");
      expect(rewardToken.vehicleId).to.equal("VEH001");
      expect(rewardToken.tokensEarned).to.equal(0);
      expect(rewardToken.tokensSpent).to.equal(0);
    });

    it("Should return total counts", async function () {
      const totalVehicles = await driveWiseLeaderboard.getTotalVehicles();
      const totalRecords = await driveWiseLeaderboard.getTotalComplianceRecords();
      
      expect(totalVehicles).to.be.greaterThan(0);
      expect(totalRecords).to.equal(0); // No records yet
    });
  });
}); 