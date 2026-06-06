"""
Main Flask application - Contains multiple bugs for demonstration.
"""
from flask import Flask, jsonify, request
from src.services.order_service import OrderService
from src.models.user import User

app = Flask(__name__)
order_service = OrderService()

@app.route('/api/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """
    Get all orders for a user.
    
    BUG 1: Doesn't handle case when user has no orders (returns None)
    BUG 2: No error handling for invalid user_id
    """
    user = User.get_by_id(user_id)
    orders = order_service.get_orders_by_user(user.id)
    
    # BUG: This will crash if orders is None
    order_list = [order.to_dict() for order in orders]
    
    return jsonify({
        'user_id': user_id,
        'orders': order_list
    })

@app.route('/api/orders/<int:order_id>/total', methods=['GET'])
def calculate_order_total(order_id):
    """
    Calculate order total with discount.
    
    BUG 3: Division by zero when discount is 100%
    BUG 4: No validation for negative prices
    """
    order = order_service.get_order(order_id)
    
    total = sum(item['price'] * item['quantity'] for item in order['items'])
    discount_percent = order.get('discount', 0)
    
    # BUG: Division by zero when discount is 100
    final_total = total / (1 - discount_percent / 100)
    
    return jsonify({
        'order_id': order_id,
        'total': final_total
    })

@app.route('/api/users/<int:user_id>/recent-orders', methods=['GET'])
def get_recent_orders(user_id):
    """
    Get recent orders for a user.
    
    BUG 5: Array index out of bounds
    BUG 6: Doesn't handle missing 'limit' parameter
    """
    limit = int(request.args['limit'])  # BUG: KeyError if not provided
    orders = order_service.get_orders_by_user(user_id)
    
    # BUG: Crashes if orders has fewer items than limit
    recent = orders[:limit]
    
    return jsonify({
        'orders': [order.to_dict() for order in recent]
    })

if __name__ == '__main__':
    app.run(debug=True)