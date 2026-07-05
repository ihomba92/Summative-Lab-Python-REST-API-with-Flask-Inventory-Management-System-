from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Temporary in-memory storage
temporary_inventory = [
    {"id": 1, "name": "Item A", "quantity": 100, "Barcode": "1234567890123", "Price": 9.99},
    {"id": 2, "name": "Item B", "quantity": 200, "Barcode": "1234567890124", "Price": 19.99}
]

BASE_URL = "https://world.openfoodfacts.org/api/v2/product"
HEADERS = {
    "User-Agent": "InventoryManagement/1.0 (learning project)"
}

def fetch_external_product_data(barcode):
    """
    Fetches product details from Open Food Facts using the barcode.
    """
    try:
        # Open Food Facts URL structure: BASE_URL/{barcode}.json
        response = requests.get(f"{BASE_URL}/{barcode}.json", headers=HEADERS, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:  # Open Food Facts returns status 1 if product is found
                product = data.get("product", {})
                return {
                    "name": product.get("product_name", "Unknown External Product"),
                    # Open Food Facts doesn't track retail prices, so we provide a default
                    "Price": 5.00 
                }
    except Exception as e:
        print(f"Error fetching from Open Food Facts: {e}")
    
    return None

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Inventory Management System!"})

@app.route('/inventory', methods=['GET'])
def get_inventory():
    return jsonify(temporary_inventory)

@app.route('/inventory', methods=['POST'])
def add_inventory_item():
    item_data = request.get_json()
    barcode = item_data.get("Barcode")
    name = item_data.get("name")
    price = item_data.get("Price")

    # If the user provided a barcode but no name/price, fetch it from Open Food Facts!
    if barcode and not name:
        print(f"Fetching details for barcode {barcode} from Open Food Facts...")
        external_data = fetch_external_product_data(barcode)
        
        if external_data:
            name = external_data["name"]
            price = price if price else external_data["Price"]
        else:
            name = name if name else "Unknown Product"
            price = price if price else 0.00

    # Generate unique ID
    new_item_id = max([i['id'] for i in temporary_inventory], default=0) + 1
    
    new_item = {
        "id": new_item_id,
        "name": name,
        "quantity": item_data.get("quantity", 1), # Default to 1 if not provided
        "Barcode": barcode,
        "Price": price
    }
    
    temporary_inventory.append(new_item)
    return jsonify({"message": "Item added successfully", "item": new_item}), 201

@app.route('/inventory/<int:item_id>', methods=['GET'])
def get_inventory_item(item_id):
    item = next((i for i in temporary_inventory if i["id"] == item_id), None)
    return jsonify(item) if item else (jsonify({"error": "Item not found"}), 404)

@app.route('/inventory/<int:item_id>', methods=['PATCH'])
def update_inventory_item(item_id):
    item_data = request.get_json()
    item = next((i for i in temporary_inventory if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    for key, value in item_data.items():
        if key in item and key != 'id':
            item[key] = value
    return jsonify({"message": f"Item {item_id} updated successfully", "updated_data": item})  

@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    global temporary_inventory
    item = next((i for i in temporary_inventory if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    temporary_inventory = [i for i in temporary_inventory if i["id"] != item_id]
    return jsonify({"message": f"Item {item_id} deleted successfully"}) 

if __name__ == '__main__':
    app.run(debug=True)