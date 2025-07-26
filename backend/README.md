# Project Documentation

## Overview
This project is a smart contract application built using Hardhat. It manages various vehicle-related data properties such as speed limits, horn usage, and safety features.

## Project Structure
- **contracts/**: Contains the smart contract files.
  - `Data.sol`: The main smart contract that manages vehicle data.
  
- **scripts/**: Contains deployment scripts.
  - `deploy.js`: Script to deploy the `Data` contract to the blockchain.
  
- **test/**: Contains test files for the smart contracts.
  - `Data.test.js`: Test cases for the `Data` contract.
  
- **hardhat.config.js**: Configuration file for Hardhat, specifying network settings and compiler options.

- **package.json**: Lists the project dependencies and scripts for managing the project.

## Getting Started

### Prerequisites
- Node.js (version 12 or later)
- npm (Node package manager)

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/microsoft/vscode-extension-samples.git
   cd vscode-extension-samples/backend
   ```

2. Install the dependencies:
   ```
   npm install
   ```

### Running the Project
- To compile the smart contracts, run:
  ```
  npx hardhat compile
  ```

- To deploy the smart contract, run:
  ```
  npx hardhat run scripts/deploy.js
  ```

- To run the tests, execute:
  ```
  npx hardhat test
  ```

## Usage
The `Data` smart contract allows you to manage the following properties:
- `speedLimit`: The maximum speed limit (uint).
- `speed`: The current speed (uint).
- `noHornArea`: Indicates if the area is a no horn zone (bool).
- `didWeHorned`: Indicates if the horn was used (bool).
- `hump`: Indicates if there is a speed hump (bool).
- `fourWheeler`: Indicates if the vehicle is a four-wheeler (bool).
- `seatbelt`: Indicates if the seatbelt is fastened (bool).

You can interact with the contract through the deployed instance on the blockchain.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.