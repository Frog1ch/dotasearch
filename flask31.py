from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
from database import db, Action

app = Flask(__name__, static_url_path='')
CORS(app)

# Get the base directory for the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///actions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables on startup
with app.app_context():
    db.create_all()

# Load products from JSON file
def load_products():
    try:
        products_path = os.path.join(BASE_DIR, 'products.json')
        with open(products_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'products': []}

# Save products to JSON file
def save_products(products):
    products_path = os.path.join(BASE_DIR, 'products.json')
    with open(products_path, 'w') as f:
        json.dump(products, f, indent=4)

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(BASE_DIR, 'admin.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(BASE_DIR, path)

# Get all products or filter by category
@app.route('/api/products', methods=['GET'])
def get_products():
    category = request.args.get('category', 'all')
    products = load_products()
    
    if category == 'all':
        return jsonify(products)
    
    filtered_products = {
        'products': [p for p in products['products'] if p['category'].lower() == category.lower()]
    }
    return jsonify(filtered_products)

# Add new product
@app.route('/api/products', methods=['POST'])
def add_product():
    try:
        new_product = request.json
        products = load_products()
        
        # Generate new ID
        max_id = max([p['id'] for p in products['products']], default=0)
        new_product['id'] = max_id + 1
        
        # Validate required fields
        required_fields = ['name', 'price', 'description', 'category', 'image', 'inventory']
        for field in required_fields:
            if field not in new_product:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate inventory format
        if not isinstance(new_product['inventory'], dict):
            return jsonify({'error': 'Inventory must be an object with size quantities'}), 400
        
        products['products'].append(new_product)
        save_products(products)
        
        return jsonify(new_product), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Update product
@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        updated_product = request.json
        products = load_products()
        
        for i, product in enumerate(products['products']):
            if product['id'] == product_id:
                # Update fields while preserving ID
                updated_product['id'] = product_id
                products['products'][i] = updated_product
                save_products(products)
                return jsonify(updated_product)
        
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Delete product
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        products = load_products()
        
        for i, product in enumerate(products['products']):
            if product['id'] == product_id:
                del products['products'][i]
                save_products(products)
                return '', 204
        
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Process order
@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        order_data = request.json
        products = load_products()
        
        # Validate order data
        if not order_data.get('items'):
            return jsonify({'error': 'No items in order'}), 400
        
        # Check inventory and calculate total
        total = 0
        inventory_updates = {}
        
        for item in order_data['items']:
            product_id = item['productId']
            size = item['size']
            quantity = item['quantity']
            
            # Find product
            product = next((p for p in products['products'] if p['id'] == product_id), None)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            # Check inventory
            if size not in product['inventory']:
                return jsonify({'error': f'Size {size} not available for product {product_id}'}), 400
            
            if product['inventory'][size] < quantity:
                return jsonify({'error': f'Insufficient inventory for product {product_id} size {size}'}), 400
            
            # Track inventory updates
            if product_id not in inventory_updates:
                inventory_updates[product_id] = {'product': product, 'updates': {}}
            inventory_updates[product_id]['updates'][size] = quantity
            
            # Add to total
            total += product['price'] * quantity
        
        # Update inventory
        for product_id, update in inventory_updates.items():
            product = update['product']
            for size, quantity in update['updates'].items():
                product['inventory'][size] -= quantity
        
        # Save updated inventory
        save_products(products)
        
        # Create order record
        order = {
            'id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'items': order_data['items'],
            'total': total,
            'status': 'confirmed',
            'telegramUserId': order_data.get('telegramUserId'),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'order': order, 'message': 'Order processed successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Action endpoints
@app.route('/api/actions', methods=['GET'])
def get_actions():
    actions = Action.query.filter_by(is_active=True).order_by(Action.created_at.desc()).all()
    return jsonify([action.to_dict() for action in actions])

@app.route('/api/actions', methods=['POST'])
def create_action():
    try:
        data = request.json
        if not data.get('title') or not data.get('description'):
            return jsonify({'error': 'Title and description are required'}), 400

        new_action = Action(
            title=data['title'],
            description=data['description'],
            image_url=data.get('image_url')
        )
        db.session.add(new_action)
        db.session.commit()
        return jsonify(new_action.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/actions/<int:action_id>', methods=['DELETE'])
def delete_action(action_id):
    try:
        action = Action.query.get_or_404(action_id)
        action.is_active = False
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
