"""Order service - Contains business logic bugs."""
from typing import List, Optional, Dict
from datetime import datetime

class Order:
    def __init__(self, id: int, user_id: int, items: List[Dict], created_at: datetime):
        self.id = id
        self.user_id = user_id
        self.items = items
        self.created_at = created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': self.items,
            'created_at': self.created_at.isoformat()
        }

class OrderService:
    def __init__(self):
        self.orders = self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock order data."""
        return [
            Order(1, 100, [{'name': 'Book', 'price': 10, 'quantity': 2}], datetime.now()),
            Order(2, 101, [{'name': 'Pen', 'price': 2, 'quantity': 5}], datetime.now()),
        ]
    
    def get_orders_by_user(self, user_id: int) -> Optional[List[Order]]:
        """
        Get orders for a user.
        
        BUG: Returns None instead of empty list when user has no orders.
        This causes AttributeError in calling code.
        """
        user_orders = [order for order in self.orders if order.user_id == user_id]
        
        # BUG: Should return [] instead of None
        if not user_orders:
            return None
        
        return user_orders
    
    def get_order(self, order_id: int) -> Dict:
        """
        Get order by ID.
        
        BUG: Returns None if order not found, but calling code expects dict.
        """
        for order in self.orders:
            if order.id == order_id:
                return {
                    'id': order.id,
                    'items': order.items,
                    'discount': 0
                }
        
        # BUG: Should raise exception or return default dict
        return None