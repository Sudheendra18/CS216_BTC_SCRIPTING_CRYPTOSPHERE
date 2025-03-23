from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import sys
import time
from decimal import Decimal

# RPC connection details
RPC_USER = "vikas"
RPC_PASSWORD = "saru"
RPC_HOST = "127.0.0.1"
RPC_PORT = "18443"
WALLET_NAME = "project"  # Explicitly use this wallet

def connect_to_rpc():
    """Connect to Bitcoin Core RPC with correct authentication."""
    rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    
    print("\n------------------------------------------------------------")
    print("|    LEGACY P2PKH TRANSACTION SCRIPT (B → C) ")
    print("------------------------------------------------------------")
    print(f"Connecting to Bitcoin Core at {rpc_url}")
    print("------------------------------------------------------------")
    
    return AuthServiceProxy(rpc_url)

def load_wallet(rpc_connection, wallet_name=WALLET_NAME):
    """Load an existing wallet."""
    try:
        wallet_list = rpc_connection.listwallets()
        if wallet_name not in wallet_list:
            print(f"Loading wallet: {wallet_name}")
            rpc_connection.loadwallet(wallet_name)
        return AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{wallet_name}")
    except JSONRPCException as e:
        print(f"Error loading wallet: {e}")
        sys.exit(1)

def get_utxos(wallet_rpc, legacy_addresses):
    """Fetch unspent transactions (UTXOs) for given legacy_addresses."""
    utxos = wallet_rpc.listunspent(1, 9999999, legacy_addresses)
    if not utxos:
        return "[No UTXOs Found]"
    
    utxo_table = "------------------------------------------------------------\n"
    utxo_table += "| TXID                                       | VOUT | Amount       |\n"
    utxo_table += "------------------------------------------------------------\n"
    for utxo in utxos:
        utxo_table += f"| {utxo['txid'][:42]}... | {utxo['vout']:<4} | {utxo['amount']:.8f} BTC |\n"
    utxo_table += "------------------------------------------------------------"
    return utxo_table

def get_script_info(wallet_rpc, txid):
    """Get locking and unlocking script information for a transaction."""
    try:
        # Get raw transaction
        raw_tx = wallet_rpc.getrawtransaction(txid)
        # Decode the transaction to get its details
        decoded_tx = wallet_rpc.decoderawtransaction(raw_tx)
        
        # Get scriptPubKey (locking script) from first output
        locking_script = decoded_tx['vout'][0]['scriptPubKey']['hex']
        locking_asm = decoded_tx['vout'][0]['scriptPubKey']['asm']
        
        # For the unlocking script, we need the input that spends this output
        # We'll look at the scriptsig from the transaction input
        unlocking_script = ""
        unlocking_asm = ""
        
        # For the current transaction, if it's spending an input, show that input's unlocking script
        if 'vin' in decoded_tx and len(decoded_tx['vin']) > 0:
            unlocking_script = decoded_tx['vin'][0].get('scriptSig', {}).get('hex', 'No unlocking script found')
            unlocking_asm = decoded_tx['vin'][0].get('scriptSig', {}).get('asm', 'No unlocking script found')
        
        return {
            "locking_script_hex": locking_script,
            "locking_script_asm": locking_asm,
            "unlocking_script_hex": unlocking_script,
            "unlocking_script_asm": unlocking_asm,
            "decoded_tx": decoded_tx
        }
    except JSONRPCException as e:
        print(f"Error getting script info: {e}")
        return None

def main():
    rpc_connection = connect_to_rpc()
    wallet_rpc = load_wallet(rpc_connection)

    # Try to load legacy_addresses from file, or ask user to input them
    try:
        with open("legacy_addresses.txt", "r") as f:
            lines = f.readlines()
            addr_a = lines[0].strip()
            addr_b = lines[1].strip()
            addr_c = lines[2].strip()
            print(f"| legacy_Addresses Loaded     | Successfully loaded from legacy_addresses.txt")
    except:
        addr_b = input("Enter Address B (sender): ").strip()
        addr_c = input("Enter Address C (receiver): ").strip()

    print("\n------------------------------------------------------------")
    print("| STEP                 | DETAILS")
    print("------------------------------------------------------------")

    # Check available UTXOs for Address B
    utxos = wallet_rpc.listunspent(1, 9999999, [addr_b])
    if not utxos:
        print("| ERROR               | No UTXOs found for Address B.")
        print("------------------------------------------------------------")
        return

    utxo = utxos[0]  # Use the first available UTXO
    available_balance = Decimal(utxo["amount"])  # Get the amount from the UTXO

    print("| Selected UTXO        |")
    print(f"| TXID                | {utxo['txid']}")
    print(f"| VOUT                | {utxo['vout']}")
    print(f"| Amount              | {available_balance:.8f} BTC")
    print("------------------------------------------------------------")

    # Get script information for the input UTXO
    input_script_info = get_script_info(wallet_rpc, utxo['txid'])
    if input_script_info:
        print("| Source TX Locking    |")
        print(f"| Script (P2PKH)      | {input_script_info['locking_script_hex']}")
        print(f"| ASM                  | {input_script_info['locking_script_asm']}")
        print("------------------------------------------------------------")

    # Fix: Dynamically determine how much to send (use available balance)
    send_amount = min(Decimal("0.3"), available_balance - Decimal("0.0001"))  # Ensure sufficient funds

    if send_amount <= 0:
        print("| ERROR               | Not enough funds to send after fees!")
        print("------------------------------------------------------------")
        return

    change_amount = available_balance - send_amount - Decimal("0.0001")  # Subtracting transaction fee

    tx_inputs = [{"txid": utxo["txid"], "vout": utxo["vout"]}]
    tx_outputs = {addr_c: float(send_amount)}

    if change_amount > 0:
        tx_outputs[addr_b] = float(change_amount)  # Send change back to B

    raw_tx = wallet_rpc.createrawtransaction(tx_inputs, tx_outputs)
    signed_tx = wallet_rpc.signrawtransactionwithwallet(raw_tx)

    if signed_tx["complete"]:
        txid_b_to_c = wallet_rpc.sendrawtransaction(signed_tx["hex"])
        print("| Transaction B → C    |")
        print(f"| TXID                | {txid_b_to_c}")
        print("------------------------------------------------------------")
        
        # Confirm in a block
        wallet_rpc.generatetoaddress(1, addr_c)
        
        # Get script information for the B to C transaction
        output_script_info = get_script_info(wallet_rpc, txid_b_to_c)
        if output_script_info:
            print("| Unlocking Script     |")
            print(f"| HEX                  | {output_script_info['unlocking_script_hex']}")
            print(f"| ASM                  | {output_script_info['unlocking_script_asm']}")
            print("------------------------------------------------------------")
            print("| Locking Script (C)   |")
            print(f"| HEX                  | {output_script_info['locking_script_hex']}")
            print(f"| ASM                  | {output_script_info['locking_script_asm']}")
            print("------------------------------------------------------------")
            
            # Add verification explanation
            print("| Script Verification  |")
            print("| Process              | 1. Unlocking script provides signature+pubkey")
            print("|                      | 2. Pubkey hashed and compared to script hash")
            print("|                      | 3. Signature verified against pubkey")
            print("|                      | 4. If valid, Bitcoin is transferred to Address C")
            print("------------------------------------------------------------")
    else:
        print("| ERROR               | Transaction signing failed!")
        print("------------------------------------------------------------")

    # Check UTXOs after transaction
    print("| UTXOs After B → C    |")
    print(get_utxos(wallet_rpc, [addr_b, addr_c]))
    print("------------------------------------------------------------")

    # Display final balance
    wallet_balance = wallet_rpc.getbalance()
    print(f"| Final Wallet Balance | After Transactions: {wallet_balance:.8f} BTC")
    print("------------------------------------------------------------")

if __name__ == "__main__":
    main()