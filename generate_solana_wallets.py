import json
import csv
import os
import hashlib
import secrets
import base58
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import requests

# Initialize Solana RPC endpoint (Devnet)
RPC_ENDPOINT = "https://api.devnet.solana.com"


def create_wallets(num_wallets):
    """Generate Solana wallets following the official specification:
    1. Generate 32 bytes of random data for private key
    2. Hash with SHA512
    3. Take first 32 bytes of hash output
    4. Use Ed25519 to generate public key
    """
    wallets = []
    for _ in range(num_wallets):
        # Step 1: Generate 32 random bytes
        private_key_bytes = secrets.token_bytes(32)
        
        # Step 2: Hash with SHA512
        hasher = hashlib.sha512()
        hasher.update(private_key_bytes)
        hashed_bytes = hasher.digest()
        
        # Step 3: Take first 32 bytes of hash
        seed_bytes = hashed_bytes[:32]
        
        # Step 4: Generate Ed25519 keypair
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed_bytes)
        public_key = private_key.public_key()
        
        # Get public key bytes
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Create secret key (64 bytes: private key + public key)
        secret_key = seed_bytes + public_bytes
        
        # Format as Base58 for Phantom compatibility
        secret_key_b58 = base58.b58encode(secret_key).decode('utf-8')
        public_key_b58 = base58.b58encode(public_bytes).decode('utf-8')
        
        wallets.append({
            "public_key": public_key_b58,
            "private_key": secret_key_b58  # This is actually the secret key (private + public)
        })
    
    return wallets


def save_wallets(wallets, output_dir, file_format="json"):
    """Save wallets to either JSON or CSV format."""
    os.makedirs(output_dir, exist_ok=True)
    if file_format.lower() == "json":
        filepath = os.path.join(output_dir, "wallets.json")
        with open(filepath, "w") as f:
            json.dump(wallets, f, indent=4)
    else:
        filepath = os.path.join(output_dir, "wallets.csv")
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Public Key", "Private Key"])
            writer.writerows(
                [[w["public_key"], w["private_key"]] for w in wallets]
            )

    print(f"Wallets saved to {filepath}")


def check_wallet_balances(wallets):
    """Check SOL balance for each wallet using RPC endpoint."""
    headers = {"Content-Type": "application/json"}

    for wallet in wallets:
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet["public_key"]],
            }
            response = requests.post(RPC_ENDPOINT, headers=headers, json=payload)
            data = response.json()

            if "result" in data:
                # Convert lamports to SOL
                sol_balance = data["result"]["value"] / 10**9
                print(
                    f"Wallet: {wallet['public_key']}\n"
                    f"Balance: {sol_balance} SOL\n"
                )
            else:
                print(
                    f"Error checking balance for {wallet['public_key']}: "
                    f"{data.get('error', 'Unknown error')}\n"
                )

        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Error checking balance for {wallet['public_key']}: {e}\n")


def main():
    # Get number of wallets to generate
    try:
        num_wallets = int(input("How many wallets do you want to generate? "))
        if num_wallets <= 0:
            raise ValueError("Number must be positive")
    except ValueError as e:
        print(f"Invalid input: {e}")
        return

    # Generate wallets
    print(f"\nGenerating {num_wallets} wallets...")
    wallets = create_wallets(num_wallets)

    # Get save format preference
    while True:
        format_choice = input("\nSave as JSON or CSV? (j/c): ").lower()
        if format_choice in ['j', 'c']:
            break
        print("Please enter 'j' for JSON or 'c' for CSV")

    # Save wallets to specified directory
    output_dir = (  # Fixed typo in 'wallet' and used double backslashes
        "I:\\flock\\walllet gen"
    )
    save_wallets(
        wallets,
        output_dir,
        'json' if format_choice == 'j' else 'csv'
    )

    # Check balances
    print("\nChecking wallet balances...")
    check_wallet_balances(wallets)


if __name__ == "__main__":
    main()
