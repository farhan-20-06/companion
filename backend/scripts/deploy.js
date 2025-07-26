const hre = require("hardhat");

async function main() {
    const Data = await hre.ethers.getContractFactory("Data");
    const data = await Data.deploy();

    await data.deployed();

    console.log("Data contract deployed to:", data.address);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });