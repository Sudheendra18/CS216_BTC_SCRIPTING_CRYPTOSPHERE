# CS216_BTC_SCRIPTING_CRYPTOSPHERE
# Bitcoin Scripting Assignment

## Team Members
- [Sudheendra] (Roll Number: [230001076])
- [Vikas]      (Roll Number: [230002023])
- [Raja Reddy] (Roll Number: [230001054])

## Project Overview

This project demonstrates how to create, sign, and broadcast Bitcoin transactions using different address types. The implementation includes:

1. Creation and validation of Legacy (P2PKH) transactions
2. Creation and validation of SegWit (P2SH-P2WPKH) transactions 
3. Analysis and comparison between the transaction types

All code runs in Bitcoin's regtest environment for safe testing without using real Bitcoin.

## Requirements

### Software Dependencies
- Bitcoin Core (bitcoind) 25.0 or later
- Python 3.8+
- `python-bitcoinrpc` library

### Python Dependencies
Install required Python packages:
```bash
pip install python-bitcoinrpc
```

## Bitcoin Core Configuration

Before running the scripts, ensure Bitcoin Core is properly configured in regtest mode:

1. Create or modify `bitcoin.conf` file in your Bitcoin data directory:
```
# Network
regtest=1
server=1
txindex=1

# RPC Configuration
rpcuser=vikas
rpcpassword=saru
rpcport=18443
rpcallowip=127.0.0.1

# Fee Configuration
paytxfee=0.0001
fallbackfee=0.0002
mintxfee=0.00001
txconfirmtarget=1
```

2. Start Bitcoin Core in regtest mode:
```bash
bitcoind -regtest 
```

3. Create a new wallet named "project" for the assignment:
```bash
bitcoin-cli -regtest createwallet project
```

## Running the Scripts

The scripts should be run in the following sequence:

### 1. Legacy (P2PKH) Transactions

First, generate the legacy addresses and create a transaction from address A to B:

```bash
python legacy_AB.py
```

This script will:
- Connect to bitcoind's RPC interface
- Create three legacy addresses (A, B, C)
- Fund address A with 1 BTC
- Create and broadcast a transaction sending 0.5 BTC from A to B
- Save the generated addresses to `legacy_addresses.txt`
- Display the transaction details and locking script information

Next, create a transaction from address B to C:

```bash
python legacy_BC.py
```

This script will:
- Read addresses from `legacy_addresses.txt`
- Find UTXOs belonging to address B
- Create and broadcast a transaction from B to C
- Display both the unlocking and locking scripts
- Provide script verification details

### 2. SegWit (P2SH-P2WPKH) Transactions

First, generate the SegWit addresses and create a transaction from address A' to B':

```bash
python segwit_AB.py
```

This script will:
- Connect to bitcoind's RPC interface
- Create three P2SH-SegWit addresses (A', B', C')
- Fund address A' with 1 BTC
- Create and broadcast a transaction sending 0.5 BTC from A' to B'
- Save the generated addresses to `segwit_addresses.txt`
- Display the transaction details and P2SH-SegWit locking script information

Next, create a transaction from address B' to C':

```bash
python segwit_BC.py
```

This script will:
- Read addresses from `segwit_addresses.txt`
- Find UTXOs belonging to address B'
- Create and broadcast a transaction from B' to C'
- Display the unlocking script, witness data, and locking script
- Provide SegWit script verification details

## Understanding the Script Output

### For Legacy (P2PKH) Transactions:

The scripts will display:
- Transaction IDs (TXIDs)
- Address information
- UTXO details
- Locking script (scriptPubKey) in both hex and ASM format
- Unlocking script (scriptSig) in both hex and ASM format
- Verification process explanation

#### Example P2PKH Locking Script (scriptPubKey):
```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

#### Example P2PKH Unlocking Script (scriptSig):
```
<signature> <pubKey>
```

### For SegWit (P2SH-P2WPKH) Transactions:

The scripts will display:
- Transaction IDs (TXIDs)
- Address information
- UTXO details
- P2SH locking script (scriptPubKey) in both hex and ASM format
- Witness data containing the signature and public key
- Unlocking script (scriptSig) with the redeemScript
- Verification process explanation

#### Example P2SH-SegWit Locking Script (scriptPubKey):
```
OP_HASH160 <scriptHash> OP_EQUAL
```
#### Example P2SH-SegWit Unlocking Script (scriptSig):
```
<redeemScript>
```
#### Example Witness Data:
```
<signature>
<pubKey>
```

## Key Differences Between Legacy and SegWit

1. **Script Structure**:
   - Legacy P2PKH: Both signature and public key are in the scriptSig (unlocking script)
   - SegWit: Signature and public key are moved to the witness data, keeping scriptSig minimal
2. **Transaction Size**:
   - SegWit transactions separate signature data (witness data) from transaction data
   - This results in smaller transaction sizes and lower fees
3. **Security**:
   - SegWit addresses fix transaction malleability issues by moving signatures outside the transaction hash
   - This enables safer second-layer protocols like Lightning Network

## Troubleshooting

If you encounter issues:
1. **RPC Connection Problems**:
   - Ensure bitcoind is running in regtest mode
   - Verify RPC credentials match those in the scripts
   - Check if the wallet "project" exists and is loaded
2. **Insufficient Funds**:
   - In regtest mode, you may need to generate blocks to confirm transactions:
   ```bash
   bitcoin-cli -regtest generatetoaddress 101 $(bitcoin-cli -regtest getnewaddress)
   ```
3. **Script Execution Order**:
   - Scripts must be run in the correct sequence (AB scripts before BC scripts)
   - The address files created by AB scripts are required for BC scripts
  
   - Wallet Info
     
![RM1](https://github.com/user-attachments/assets/e14f4419-a4bb-4740-8d3b-baa2d596d131)

   - UTXO of Legacy

![RM2](https://github.com/user-attachments/assets/f720bb18-6de3-48fc-9b7f-2a3c173292e4)
   
   - UTXO of Segwit

![RM3](https://github.com/user-attachments/assets/5b83d08b-9e5b-4c7f-90e1-547e327328f4)
