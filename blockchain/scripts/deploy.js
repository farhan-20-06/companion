const hre = require("hardhat");

async function main() {
  console.log("Deploying DriveWise Leaderboard contract...");

  // Get the contract factory
  const DriveWiseLeaderboard = await hre.ethers.getContractFactory("DriveWiseLeaderboard");
  
  // Deploy the contract
  const leaderboard = await DriveWiseLeaderboard.deploy();
  
  // Wait for deployment to finish
  await leaderboard.waitForDeployment();
  
  const address = await leaderboard.getAddress();
  console.log("DriveWise Leaderboard deployed to:", address);
  
  // Log deployment info
  console.log("Contract Address:", address);
  console.log("Network:", hre.network.name);
  
  // Verify the contract on Etherscan (if not on localhost)
  if (hre.network.name !== "localhost" && hre.network.name !== "hardhat") {
    console.log("Waiting for block confirmations...");
    await leaderboard.deploymentTransaction().wait(6);
    await verify(address, []);
  }
}

// Verify function for Etherscan
async function verify(contractAddress, args) {
  console.log("Verifying contract...");
  try {
    await hre.run("verify:verify", {
      address: contractAddress,
      constructorArguments: args,
    });
  } catch (e) {
    if (e.message.toLowerCase().includes("already verified")) {
      console.log("Already verified!");
    } else {
      console.log(e);
    }
  }
}

// Handle errors
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
}); 