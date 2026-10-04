"""
Weekly Mini Project 01
Cybersecurity Asset Inventory System

This program lets a security admin keep track of the organization's
IT assets (workstations, servers, routers, switches, applications).
You can add, search, update, delete and display assets, and it also
gives a small security summary at the end so you can see how many
assets are risky.

Data is saved to data/assets.json so it doesn't disappear every time
you close the program.

Author: BAGATHEESHWAR A
"""

import json
import os

# path to the json file where all assets are stored
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "assets.json")

# allowed values - using these so the user can't just type garbage
ASSET_TYPES = ["Workstation", "Server", "Router", "Switch", "Application"]
RISK_LEVELS = ["Low", "Medium", "High", "Critical"]
SECURITY_STATUSES = ["Secure", "Warning", "Vulnerable"]


def load_assets():
    """Load assets from the json file. If the file doesn't exist yet,
    just return an empty list so the program still works on first run."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # if the file got corrupted somehow, don't crash, just start fresh
        print("Warning: could not read existing data file, starting empty.")
        return []


def save_assets(assets):
    """Save the current list of assets back to the json file."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(assets, f, indent=4)


def get_valid_choice(prompt, options):
    """Keep asking the user until they type one of the valid options.
    Used for asset type / risk level / security status so we don't
    end up with typos in the data."""
    options_str = "/".join(options)
    while True:
        choice = input(f"{prompt} ({options_str}): ").strip()
        # allow case-insensitive matching, but store the proper case
        for opt in options:
            if choice.lower() == opt.lower():
                return opt
        print(f"Invalid choice. Please pick one of: {options_str}")


def asset_id_exists(assets, asset_id):
    for a in assets:
        if a["asset_id"].lower() == asset_id.lower():
            return True
    return False


def add_asset(assets):
    print("\n--- Add New Asset ---")

    asset_id = input("Asset ID: ").strip()
    if asset_id == "":
        print("Asset ID cannot be empty. Cancelling add.")
        return

    if asset_id_exists(assets, asset_id):
        print(f"An asset with ID '{asset_id}' already exists. Use update instead.")
        return

    name = input("Asset Name: ").strip()
    asset_type = get_valid_choice("Asset Type", ASSET_TYPES)
    ip_address = input("IP Address: ").strip()
    os_name = input("Operating System: ").strip()
    department = input("Owner/Department: ").strip()
    risk_level = get_valid_choice("Risk Level", RISK_LEVELS)
    status = get_valid_choice("Security Status", SECURITY_STATUSES)

    new_asset = {
        "asset_id": asset_id,
        "asset_name": name,
        "asset_type": asset_type,
        "ip_address": ip_address,
        "os": os_name,
        "department": department,
        "risk_level": risk_level,
        "status": status
    }

    assets.append(new_asset)
    save_assets(assets)
    print(f"Asset '{asset_id}' added successfully.\n")


def print_asset(asset):
    print("-----------------------------------------")
    print(f"Asset ID    : {asset['asset_id']}")
    print(f"Asset Name  : {asset['asset_name']}")
    print(f"Asset Type  : {asset['asset_type']}")
    print(f"IP Address  : {asset['ip_address']}")
    print(f"OS          : {asset['os']}")
    print(f"Department  : {asset['department']}")
    print(f"Risk Level  : {asset['risk_level']}")
    print(f"Status      : {asset['status']}")


def display_assets(assets):
    print("\n=========================================")
    print(" CYBERSECURITY ASSET INVENTORY")
    print("=========================================")

    if len(assets) == 0:
        print("No assets found.")
    else:
        for asset in assets:
            print_asset(asset)

    print("-----------------------------------------")
    print_summary(assets)
    print("=========================================\n")


def print_summary(assets):
    total = len(assets)
    critical = sum(1 for a in assets if a["risk_level"] == "Critical")
    high = sum(1 for a in assets if a["risk_level"] == "High")
    medium = sum(1 for a in assets if a["risk_level"] == "Medium")
    low = sum(1 for a in assets if a["risk_level"] == "Low")
    vulnerable = sum(1 for a in assets if a["status"] == "Vulnerable")

    print(f"Total Assets      : {total}")
    print(f"Critical Assets   : {critical}")
    print(f"High Risk Assets  : {high}")
    print(f"Medium Risk Assets: {medium}")
    print(f"Low Risk Assets   : {low}")
    print(f"Vulnerable Assets : {vulnerable}")


def search_asset(assets):
    print("\n--- Search Asset ---")
    keyword = input("Enter Asset ID or Asset Name to search: ").strip().lower()

    results = []
    for a in assets:
        if keyword in a["asset_id"].lower() or keyword in a["asset_name"].lower():
            results.append(a)

    if len(results) == 0:
        print("No matching assets found.\n")
        return

    print(f"\nFound {len(results)} matching asset(s):")
    for a in results:
        print_asset(a)
    print("-----------------------------------------\n")


def find_asset_by_id(assets, asset_id):
    for a in assets:
        if a["asset_id"].lower() == asset_id.lower():
            return a
    return None


def update_asset(assets):
    print("\n--- Update Asset ---")
    asset_id = input("Enter Asset ID to update: ").strip()
    asset = find_asset_by_id(assets, asset_id)

    if asset is None:
        print(f"No asset found with ID '{asset_id}'.\n")
        return

    print("Leave a field blank to keep it unchanged.")

    new_name = input(f"Asset Name [{asset['asset_name']}]: ").strip()
    if new_name != "":
        asset["asset_name"] = new_name

    new_ip = input(f"IP Address [{asset['ip_address']}]: ").strip()
    if new_ip != "":
        asset["ip_address"] = new_ip

    new_os = input(f"Operating System [{asset['os']}]: ").strip()
    if new_os != "":
        asset["os"] = new_os

    new_dept = input(f"Department [{asset['department']}]: ").strip()
    if new_dept != "":
        asset["department"] = new_dept

    change_risk = input(f"Change Risk Level? currently {asset['risk_level']} (y/n): ").strip().lower()
    if change_risk == "y":
        asset["risk_level"] = get_valid_choice("New Risk Level", RISK_LEVELS)

    change_status = input(f"Change Security Status? currently {asset['status']} (y/n): ").strip().lower()
    if change_status == "y":
        asset["status"] = get_valid_choice("New Security Status", SECURITY_STATUSES)

    save_assets(assets)
    print(f"Asset '{asset_id}' updated successfully.\n")


def delete_asset(assets):
    print("\n--- Delete Asset ---")
    asset_id = input("Enter Asset ID to delete: ").strip()
    asset = find_asset_by_id(assets, asset_id)

    if asset is None:
        print(f"No asset found with ID '{asset_id}'.\n")
        return

    confirm = input(f"Are you sure you want to delete '{asset_id}'? (y/n): ").strip().lower()
    if confirm == "y":
        assets.remove(asset)
        save_assets(assets)
        print("Asset deleted.\n")
    else:
        print("Delete cancelled.\n")


def show_menu():
    print("=========================================")
    print(" CYBERSECURITY ASSET INVENTORY SYSTEM")
    print("=========================================")
    print("1. Add Asset")
    print("2. Display All Assets")
    print("3. Search Asset")
    print("4. Update Asset")
    print("5. Delete Asset")
    print("6. Exit")


def main():
    assets = load_assets()
    print("Welcome to the Cybersecurity Asset Inventory System.")

    while True:
        show_menu()
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            add_asset(assets)
        elif choice == "2":
            display_assets(assets)
        elif choice == "3":
            search_asset(assets)
        elif choice == "4":
            update_asset(assets)
        elif choice == "5":
            delete_asset(assets)
        elif choice == "6":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice, please enter a number between 1 and 6.\n")


if __name__ == "__main__":
    main()
