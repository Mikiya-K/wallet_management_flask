import os
import json
from app.models.wallet import Wallet
from app.models.miners import Miners

class Wallet_data:
    def __init__(self, coldkey_name, coldkey_address):
        self.coldkey_name = coldkey_name
        self.coldkey_address = coldkey_address
    def __repr__(self):
        # Customize the string representation for better readability
        return f"Wallet(coldkey_name='{self.coldkey_name}', coldkey_address='{self.coldkey_address}')"

class Hotkey_data:
    def __init__(self, wallet_name, hotkey_name, hotkey_address):
        self.wallet_name = wallet_name
        self.hotkey_name = hotkey_name
        self.hotkey_address = hotkey_address
    def __repr__(self):
        # Customize the string representation for better readability
        return f"Hotkey(wallet='{self.wallet_name}', name='{self.hotkey_name}', address='{self.hotkey_address}')"

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

def get_hotkey_wallets_for_path(path: str):
    """Get all hotkey information from wallet path."""
    hotkeys = []
    try:
        # Walk through the directory
        path = os.path.expanduser(path)

        for wallet_folder in os.listdir(path):
            wallet_path = os.path.join(path, wallet_folder)
            # Check if it is a directory (wallet folder)
            if not os.path.isdir(wallet_path):
                continue

            # Check if hotkeys directory exists
            hotkeys_path = os.path.join(wallet_path, 'hotkeys')
            if not os.path.exists(hotkeys_path) or not os.path.isdir(hotkeys_path):
                continue

            # Get all files in hotkeys directory
            hotkey_files = os.listdir(hotkeys_path)
            processed_hotkeys = set()  # Track processed hotkey names to avoid duplicates

            # First pass: process pub.txt files (preferred)
            for item in hotkey_files:
                if item.endswith('pub.txt'):
                    hotkey_name = item[:-7]  # Remove 'pub.txt' suffix
                    hotkeypub_file = os.path.join(hotkeys_path, item)

                    if os.path.isfile(hotkeypub_file):
                        try:
                            with open(hotkeypub_file, 'r') as file:
                                # Read and parse the hotkeypub.txt content
                                data = json.load(file)
                                hotkey_address = data.get('ss58Address', '')
                                if hotkey_address:
                                    hotkeys.append(Hotkey_data(
                                        wallet_name=wallet_folder,
                                        hotkey_name=hotkey_name,
                                        hotkey_address=hotkey_address
                                    ))
                                    processed_hotkeys.add(hotkey_name)
                        except (json.JSONDecodeError, IOError) as e:
                            print(f"Error reading pub file {hotkeypub_file}: {e}")

            # Second pass: process private key files that don't have corresponding pub files
            for item in hotkey_files:
                # Skip pub.txt files and files we've already processed
                if item.endswith('pub.txt') or item in processed_hotkeys:
                    continue

                hotkey_file = os.path.join(hotkeys_path, item)
                if os.path.isfile(hotkey_file):
                    try:
                        with open(hotkey_file, 'r') as file:
                            # Try to read as JSON (private key file format)
                            data = json.load(file)
                            hotkey_address = data.get('ss58Address', '')
                            if hotkey_address:
                                hotkeys.append(Hotkey_data(
                                    wallet_name=wallet_folder,
                                    hotkey_name=item,  # Use filename as hotkey name
                                    hotkey_address=hotkey_address
                                ))
                                processed_hotkeys.add(item)
                    except (json.JSONDecodeError, IOError) as e:
                        # Skip files that are not JSON format or can't be read
                        print(f"Skipping non-JSON file {hotkey_file}: {e}")
                        continue

    except Exception as e:
        print(f"Read Hotkeys Error: {e}")

    return hotkeys

def insert_hotkeys_to_db(hotkeys):
    """Insert hotkeys into miners table, checking if they already exist."""
    for hotkey in hotkeys:
        # Find corresponding wallet record
        wallet = Wallet.find_by_name(hotkey.wallet_name)
        if not wallet:
            print(f"Warning: Wallet '{hotkey.wallet_name}' not found in database, skipping hotkey '{hotkey.hotkey_name}'")
            continue

        # Check if the hotkey already exists in the database
        existing_miner = Miners.find_by_hotkey(hotkey.hotkey_address)
        if existing_miner:
            continue  # Skip if the hotkey already exists

        # Insert new miner into the database
        Miners.create(
            name=hotkey.hotkey_name,
            wallet=hotkey.wallet_name,
            hotkey=hotkey.hotkey_address,
            coldkey_id=wallet.id
        )
