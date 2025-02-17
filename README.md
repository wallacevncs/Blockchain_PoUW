# A Blockchain Proposal Using Matching Between Medical Residents and Hospitals as a Proof of Useful Work

## Overview

This project proposes a blockchain-based solution for the medical residency matching process. By leveraging the Proof of Useful Work (PoUW) consensus mechanism, the system improves transparency, security, and efficiency in the allocation of medical residents to hospitals. The solution integrates the stable matching algorithm (Gale-Shapley) with blockchain technology, ensuring verifiable and tamper-proof selection results.

## Features

- **Decentralized Matching Process**: Uses blockchain to ensure a fair and transparent selection process.
- **Proof of Useful Work (PoUW)**: Computing the resident-hospital matching problem as a useful workload.
- **Immutable and Verifiable Records**: Ensures trust and integrity in the matching process.
- **Hybrid Blockchain Model**: Balances decentralization with controlled access to ensure efficiency.

## Technologies Used

- **Blockchain**: Custom implementation using Python and Flask.
- **Matching Algorithm**: Gale-Shapley (Resident-Oriented) implemented via the `matching` Python library.
- **Infrastructure**: Amazon Web Services (AWS) for storage (S3), container management (ECR, ECS, Fargate).
- **Development Stack**: Python (Flask, Requests, Boto3), C# (.NET 6, Newtonsoft.Json), Docker.

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/wallacevncs/ResidentsHospitals-Matching-Generator
   ```
2. Install dependencies:
   ```sh
   pip install flask requests boto3 matching python-dateutil
   ```
3. Run the blockchain application:
   ```sh
   python app.py
   ```

## API Endpoints

- `GET /mine_block`: Mines a new block after computing the matching process.
- `GET /get_chain`: Retrieves the blockchain data.
- `POST /connect_node`: Adds a new node to the network.
- `GET /update_chain`: Synchronizes the blockchain with the network.

## Usage

1. Generate synthetic residency matching data using the [ResidentsHospitals-Matching-Generator](https://github.com/wallacevncs/ResidentsHospitals-Matching-Generator) tool.
2. Deploy the blockchain network using AWS or local Docker instances.
3. Start mining and validating residency matches with the implemented PoUW algorithm.

## License

This project is under the license [MIT](./LICENSE).

## Author

**Wallace Vinicius** - Developed as part of the Bachelor's in Computer Science at Rio de Janeiro State University (UERJ).

