from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import json

app = Flask(__name__)
CORS(app)

PRODUCTS_FILE = 'products.json'

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    return {"products": []}

def save_products(data):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Load products on startup
products_db = load_products()

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products with their current inventory."""
    category = request.args.get('category')
    if category and category != 'all':
        filtered_products = [p for p in products_db["products"] if p["category"] == category]
        return jsonify({"products": filtered_products})
    return jsonify({"products": products_db["products"]})

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product."""
    data = request.json
    required_fields = ['name', 'price', 'category', 'description']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Generate new ID
    new_id = max([p['id'] for p in products_db['products']], default=0) + 1
    
    new_product = {
        'id': new_id,
        'name': data['name'],
        'price': float(data['price']),
        'category': data['category'],
        'description': data['description'],
        'image': data.get('image', ''),
        'inventory': data.get('inventory', {})
    }
    
    products_db['products'].append(new_product)
    save_products(products_db)
    return jsonify(new_product), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product."""
    data = request.json
    product = next((p for p in products_db['products'] if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # Update fields
    for field in ['name', 'price', 'category', 'description', 'image', 'inventory']:
        if field in data:
            product[field] = data[field]
            if field == 'price':
                product[field] = float(data[field])
    
    save_products(products_db)
    return jsonify(product)

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product."""
    product = next((p for p in products_db['products'] if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    products_db['products'] = [p for p in products_db['products'] if p['id'] != product_id]
    save_products(products_db)
    return jsonify({"message": "Product deleted"})

@app.route('/api/products/<int:product_id>/inventory', methods=['PUT'])
def update_inventory(product_id):
    """Update product inventory."""
    data = request.json
    product = next((p for p in products_db['products'] if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    product['inventory'] = data
    save_products(products_db)
    return jsonify(product)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order."""
    data = request.json
    user_id = data.get('userId')
    items = data.get('items', [])
    
    if not user_id or not items:
        return jsonify({"error": "Invalid order data"}), 400

    # Validate inventory and calculate total
    total = 0
    order_items = []
    
    for item in items:
        product_id = item.get('id')
        size = item.get('size')
        product = next((p for p in products_db["products"] if p["id"] == product_id), None)
        
        if not product:
            return jsonify({"error": f"Product {product_id} not found"}), 404
        
        if size not in product["inventory"] or product["inventory"][size] < 1:
            return jsonify({"error": f"Size {size} not available for {product['name']}"}), 400
        
        # Decrease inventory
        product["inventory"][size] -= 1
        total += product["price"]
        order_items.append({
            "product_id": product_id,
            "name": product["name"],
            "size": size,
            "price": product["price"]
        })
    
    # Save updated inventory
    save_products(products_db)

    # Create order
    order = {
        "id": len(products_db.get("orders", [])) + 1,
        "user_id": user_id,
        "items": order_items,
        "total": total,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    if "orders" not in products_db:
        products_db["orders"] = []
    products_db["orders"].append(order)
    save_products(products_db)
    
    return jsonify({"order": order})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
