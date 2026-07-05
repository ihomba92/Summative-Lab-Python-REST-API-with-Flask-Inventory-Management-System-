import sys
import requests

API_URL = "http://127.0.0.1:5000/inventory"

def print_menu():
    print("\n" + "="*35)
    print("      INVENTORY MANAGEMENT CLI      ")
    print("="*35)
    print("1. View All Inventory")
    print("2. Find a Specific Item (by ID)")
    print("3. Add New Item (Local or External Lookup)")
    print("4. Update Item (Price/Stock)")
    print("5. Delete an Item")
    print("6. Exit")
    print("="*35)

def get_all_items():
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            items = response.json()
            if not items:
                print("\n[!] The inventory is currently empty.")
                return
            
            print(f"\n{'ID':<5} | {'Name':<25} | {'Quantity':<10} | {'Price':<10} | {'Barcode':<15}")
            print("-" * 75)
            for item in items:
                print(f"{item['id']:<5} | {item['name']:<25} | {item['quantity']:<10} | ${item['Price']:<9.2f} | {item['Barcode']}")
        else:
            print(f"\n[Error] Failed to fetch data. API returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to the API. Is your Flask app running?")

def find_item():
    print("\n--- Find an Item ---")
    search_term = input("Search by ID, Name, or Barcode: ").strip()
    
    if not search_term:
        print("[Invalid Input] Search term cannot be empty.")
        return

    try:
        # 1. If it's a numeric ID, we can hit the direct RESTful endpoint /inventory/<id>
        if search_term.isdigit():
            response = requests.get(f"{API_URL}/{search_term}", timeout=5)
            if response.status_code == 200:
                item = response.json()
                _print_single_item(item)
                return
            
        # 2. Fetch all items to filter by Name or Barcode locally
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            items = response.json()
            search_lower = search_term.lower()
            
            # Find all matches where search term is in the Name or exactly matches the Barcode/ID
            matches = [
                item for item in items 
                if search_lower in item.get('name', '').lower() 
                or search_term == item.get('Barcode')
                or search_term == str(item.get('id'))
            ]
            
            if not matches:
                print(f"\n[!] No items found matching '{search_term}'.")
            elif len(matches) == 1:
                _print_single_item(matches[0])
            else:
                print(f"\n[!] Found {len(matches)} matching items:")
                print(f"\n{'ID':<5} | {'Name':<25} | {'Quantity':<10} | {'Price':<10} | {'Barcode':<15}")
                print("-" * 75)
                for item in matches:
                    print(f"{item['id']:<5} | {item['name']:<25} | {item['quantity']:<10} | ${item['Price']:<9.2f} | {item['Barcode']}")
        else:
            print(f"\n[Error] API returned status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n[Error] Connection to API failed.")

def _print_single_item(item):
    """Helper function to cleanly print a single item's details."""
    print("\n--- Item Found ---")
    print(f"ID:       {item['id']}")
    print(f"Name:     {item['name']}")
    print(f"Quantity: {item['quantity']}")
    print(f"Price:    ${item['Price']:.2f}")
    print(f"Barcode:  {item['Barcode']}")

def add_item():
    print("\n--- Add New Item ---")
    barcode = input("Enter Barcode (Leave blank if none): ").strip() or None
    
    # If they pass a barcode, we can let Flask query Open Food Facts by omitting the name
    name = input("Enter Item Name (Leave blank to auto-fetch via Barcode): ").strip() or None
    
    if not name and not barcode:
        print("[Invalid Input] You must provide at least a Name or a Barcode.")
        return

    qty_input = input("Enter Quantity (Default 1): ").strip()
    try:
        quantity = int(qty_input) if qty_input else 1
    except ValueError:
        print("[Invalid Input] Quantity must be a whole number.")
        return

    price_input = input("Enter Price (Optional): ").strip()
    price = None
    if price_input:
        try:
            price = float(price_input)
        except ValueError:
            print("[Invalid Input] Price must be a valid number.")
            return

    # Build the payload dynamically
    payload = {}
    if name: payload["name"] = name
    if barcode: payload["Barcode"] = barcode
    if quantity: payload["quantity"] = quantity
    if price: payload["Price"] = price

    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 201:
            result = response.json()
            print(f"\n[Success] {result['message']}")
            print(f"Added: {result['item']['name']} (ID: {result['item']['id']})")
        else:
            print(f"\n[Error] Failed to add item. Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n[Error] Connection to API failed.")

def update_item():
    item_id = input("\nEnter the Item ID to update: ").strip()
    if not item_id.isdigit():
        print("[Invalid Input] ID must be a number.")
        return

    print("\nLeave the field blank if you don't want to change it.")
    qty_input = input("Enter New Quantity: ").strip()
    price_input = input("Enter New Price: ").strip()

    payload = {}
    if qty_input:
        if qty_input.isdigit():
            payload["quantity"] = int(qty_input)
        else:
            print("[Invalid Input] Quantity skipped (must be a whole number).")
            
    if price_input:
        try:
            payload["Price"] = float(price_input)
        except ValueError:
            print("[Invalid Input] Price skipped (must be a decimal/number).")

    if not payload:
        print("[!] No updates provided. Operation canceled.")
        return

    try:
        response = requests.patch(f"{API_URL}/{item_id}", json=payload, timeout=5)
        if response.status_code == 200:
            print(f"\n[Success] Item {item_id} updated successfully!")
        elif response.status_code == 404:
            print(f"\n[!] Item with ID {item_id} not found.")
        else:
            print(f"\n[Error] Failed to update item. Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n[Error] Connection to API failed.")

def delete_item():
    item_id = input("\nEnter the Item ID to DELETE: ").strip()
    if not item_id.isdigit():
        print("[Invalid Input] ID must be a number.")
        return

    confirm = input(f"Are you absolutely sure you want to delete item {item_id}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Deletion canceled.")
        return

    try:
        response = requests.delete(f"{API_URL}/{item_id}", timeout=5)
        if response.status_code == 200:
            print(f"\n[Success] Item {item_id} deleted successfully.")
        elif response.status_code == 404:
            print(f"\n[!] Item with ID {item_id} does not exist.")
        else:
            print(f"\n[Error] Failed to delete item. Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n[Error] Connection to API failed.")

def main():
    while True:
        print_menu()
        choice = input("Select an option (1-6): ").strip()
        
        if choice == '1':
            get_all_items()
        elif choice == '2':
            find_item()
        elif choice == '3':
            add_item()
        elif choice == '4':
            update_item()
        elif choice == '5':
            delete_item()
        elif choice == '6':
            print("\nExiting Inventory CLI. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Selection] Please choose a number between 1 and 6.")
            
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()