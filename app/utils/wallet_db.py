import os
import json
from app.models.wallet import Wallet

class Wallet_data:
    def __init__(self, coldkey_name, coldkey_address):
        self.coldkey_name = coldkey_name
        self.coldkey_address = coldkey_address
    def __repr__(self):
        # Customize the string representation for better readability
        return f"Wallet(coldkey_name='{self.coldkey_name}', coldkey_address='{self.coldkey_address}')"

def get_coldkey_wallets_for_path(path: str):
    """Get all coldkey wallet names and addresses from path."""
    wallets = []
    try:
        # Walk through the directory
        path = os.path.expanduser(path)

        for folder_name in os.listdir(path):
            folder_path = os.path.join(path, folder_name)
            # Check if it is a directory (wallet folder)
            if os.path.isdir(folder_path):
                coldkeypub_file = os.path.join(folder_path, 'coldkeypub.txt')
                if os.path.isfile(coldkeypub_file):
                    with open(coldkeypub_file, 'r') as file:
                        # Read and parse the coldkeypub.txt content
                        data = json.load(file)
                        coldkey_name = folder_name
                        coldkey_address = data.get('ss58Address', '')
                        wallets.append(Wallet_data(coldkey_name, coldkey_address))
    except Exception as e:
        print(f"Read Wallets Error: {e}")

    return wallets

def insert_wallets_to_db(wallets):
    """Insert wallets into the database, checking if they already exist."""
    for wallet in wallets:
        # Check if the wallet already exists in the database
        existing_wallet = Wallet.find_by_name(wallet.coldkey_name)

        if existing_wallet:
            continue  # Skip if the wallet already exists

        # Insert new wallet into the database
        Wallet.create(
            coldkey_name=wallet.coldkey_name,
            coldkey_address=wallet.coldkey_address
        )
