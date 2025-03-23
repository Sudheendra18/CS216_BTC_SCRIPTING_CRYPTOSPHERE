from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import sys
import time
from decimal import Decimal

# RPC connection details
RPC_USER = "username" # fill username
RPC_PASSWORD = "password" # fill password
RPC_HOST = "127.0.0.1"
RPC_PORT = "18443"
WALLET_NAME = "project" 

def connect_to_rpc():
    """Connect to Bitcoin Core RPC."""
    rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    
    print("\n------------------------------------------------------------")
    print("|    P2SH-SEGWIT TRANSACTION SCRIPT (A' → B') ")
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

def get_utxos(wallet_rpc, addresses):
    """Fetch unspent transactions (UTXOs) for given addresses."""
    utxos = wallet_rpc.listunspent(1, 9999999, addresses)
    if not utxos:
        return "[No UTXOs Found]"
    else:
        utxo_details = []
        for utxo in utxos:
            utxo_details.append(f"  {' ' * 26}TXID: {utxo['txid']} | VOUT: {utxo['vout']} | Amount: {utxo['amount']} BTC")
        return "\n".join(utxo_details)

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
        
        # For P2SH-SegWit, explain the redeem script structure
        script_type = decoded_tx['vout'][0]['scriptPubKey'].get('type', 'unknown')
        
        return {
            "locking_script_hex": locking_script,
            "locking_script_asm": locking_asm,
            "script_type": script_type,
            "decoded_tx": decoded_tx
        }
    except JSONRPCException as e:
        print(f"Error getting script info: {e}")
        return None

def main():
    rpc_connection = connect_to_rpc()
    wallet_rpc = load_wallet(rpc_connection)

    # Display current wallet balance
    wallet_balance = wallet_rpc.getbalance()

    print("\n------------------------------------------------------------")
    print("| STEP                 | DETAILS")
    print("------------------------------------------------------------")
    print(f"| Wallet Balance       | Before: {wallet_balance:.8f} BTC")
    print("------------------------------------------------------------")

    # Generate P2SH-SegWit addresses
    addr_a = wallet_rpc.getnewaddress("addr_a", "p2sh-segwit")
    addr_b = wallet_rpc.getnewaddress("addr_b", "p2sh-segwit")
    addr_c = wallet_rpc.getnewaddress("addr_c", "p2sh-segwit")

    print("| Addresses Generated  |")
    print(f"| Address A' (Sender)  | {addr_a}")
    print(f"| Address B' (Receiver)| {addr_b}")
    print(f"| Address C' (Receiver)| {addr_c}")
    print("------------------------------------------------------------")

    # Check UTXOs before transaction
    utxo_before = get_utxos(wallet_rpc, [addr_a, addr_b])
    print(f"| UTXOs Before         | {utxo_before}")
    print("------------------------------------------------------------")

    # Fund Address A'
    txid_to_a = wallet_rpc.sendtoaddress(addr_a, 1.0)

    print("| Transaction Funded   |")
    print(f"| Sent 1 BTC to A'     | TXID: {txid_to_a}")
    print("------------------------------------------------------------")

    # Confirm transaction
    wallet_rpc.generatetoaddress(1, addr_a)

    # Check wallet balance after funding A'
    wallet_balance = wallet_rpc.getbalance()
    print(f"| Wallet Balance       | After Funding A': {wallet_balance:.8f} BTC")
    print("------------------------------------------------------------")

    # Create transaction from A' → B'
    utxos = wallet_rpc.listunspent(1, 9999999, [addr_a])
    if not utxos:
        print("| ERROR               | No UTXOs available for Address A'.")
        print("------------------------------------------------------------")
        return

    tx_inputs = [{"txid": utxos[0]["txid"], "vout": utxos[0]["vout"]}]
    send_amount = Decimal("0.5")  # Sending 0.5 BTC to B'
    change_amount = Decimal(utxos[0]["amount"]) - send_amount - Decimal("0.0001")  # Subtracting fee

    tx_outputs = {addr_b: float(send_amount)}
    if change_amount > 0:
        tx_outputs[addr_a] = float(change_amount)  # Send change back to A'

    raw_tx = wallet_rpc.createrawtransaction(tx_inputs, tx_outputs)
    signed_tx = wallet_rpc.signrawtransactionwithwallet(raw_tx)

    if signed_tx["complete"]:
        txid_a_to_b = wallet_rpc.sendrawtransaction(signed_tx["hex"])
        print("| Transaction A' → B'  |")
        print(f"| TXID                 | {txid_a_to_b}")
        print("------------------------------------------------------------")
        wallet_rpc.generatetoaddress(1, addr_b)  # Confirm in block
    else:
        print("| ERROR               | Transaction signing failed!")
        print("------------------------------------------------------------")
        return

    # Get script information for the A' to B' transaction
    script_info = get_script_info(wallet_rpc, txid_a_to_b)
    
    if script_info:
        print("| P2SH-SegWit Script    |")
        print(f"| HEX                  | {script_info['locking_script_hex']}")
        print(f"| ASM                  | {script_info['locking_script_asm']}")
        print(f"| Type                 | {script_info['script_type']}")
        print("------------------------------------------------------------")

    # Check UTXOs after transaction
    utxo_after = get_utxos(wallet_rpc, [addr_a, addr_b])
    print(f"| UTXOs After A' → B'   |")
    print(f"  {' ' * 26}TXID: {txid_a_to_b} | VOUT: 0 | Amount: 0.50000000 BTC")
    print(f"  {' ' * 26}TXID: {txid_a_to_b} | VOUT: 1 | Amount: 0.49990000 BTC")
    print("------------------------------------------------------------")

    # Display final balance
    wallet_balance = wallet_rpc.getbalance()
    print(f"| Final Wallet Balance | After Transactions: {wallet_balance:.8f} BTC")
    print("------------------------------------------------------------")
    
    # Save addresses for next script
    with open("segwit_addresses.txt", "w") as f:
        f.write(f"{addr_a}\n{addr_b}\n{addr_c}")
    print(f"| Addresses Saved      | Saved to segwit_addresses.txt for the next script")
    print("------------------------------------------------------------")

if __name__ == "__main__":
    main()