from web3 import Web3
import os
import random
import json
from eth_account import Account

# Configuration
with open("key.txt") as keyFile:
    private_key = keyFile.read()
with open("rpc.txt") as rpcFile:
    rpc_url = rpcFile.read()
contract_address = '0xD590Dd57BA41D6164C6049E094B9343580A899b2'
with open('abi.json', 'r') as f3:
    contract_abi = json.load(f3)


# Setup web3 connection
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Ensure connection is successful
if not w3.is_connected():
    print("Failed to connect to Ethereum node.")
    exit()

# Load contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Account setup
account = Account.from_key(private_key)

def mint(signer, contract):
    nonce = w3.eth.get_transaction_count(account.address)
    
    challenge_number = contract.functions.challengeNumber().call()
    difficulty = contract.functions.difficulty().call()
    target = 2**(256 - difficulty)

    print("\n==============================")
    print("=     BlastPoW Miner v0.1    =")
    print("==============================")
    
    print("challenge_number:",str(challenge_number.hex()))
    print("difficulty:",difficulty)
    print("target:",target)

    mint_nonce = random.randint(0, 2**64)
    base_nonce = 0

    while True:
        base_nonce += 1
        print("nonce:"+str(base_nonce), end="\r")
        hash_hex = Web3.solidity_keccak(['bytes32', 'address', 'uint256'], [challenge_number, signer.address, mint_nonce])
        print("hash:"+str(hash_hex.hex()), end="\r")
        
        if int.from_bytes(hash_hex, byteorder='big') < target:
            print(f"Found valid nonce: {mint_nonce} (attempts: {base_nonce})")
            try:
                tx = contract.functions.mint(mint_nonce).build_transaction({
                    'from': signer.address,
                    'value': w3.to_wei(0.001, 'ether'),                    
                    'nonce': nonce,
                    'gasPrice': w3.eth.gas_price
                })
                signed_tx = signer.sign_transaction(tx)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_receipt  = w3.eth.wait_for_transaction_receipt(tx_hash)
                if tx_receipt['status'] == 1:
                    print(f"Mint successful! Transaction hash: {tx_hash.hex()}")
                else:
                    print("Mint failed!")
                break
            except Exception as e:
                print(f"Error during minting: {e}")
                # Handle specific errors here (e.g., nonce already used, hash does not meet difficulty)
                mint_nonce = random.randint(0, 2**64)  # Adjust nonce on failure
        else:
            mint_nonce += 1

        if base_nonce % 10000 == 0:
            challenge_number = contract.functions.challengeNumber().call()
            difficulty = contract.functions.difficulty().call()
            target = 2**(256 - difficulty)

while True:
    mint(account, contract)
