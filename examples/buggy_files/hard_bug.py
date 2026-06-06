"""
HARD BUG: Race condition simulation + complex logic error
Expected to have subtle bugs in async operations and data consistency
"""

import json
from datetime import datetime
from typing import List, Dict, Optional

class InventoryManager:
    """Manages product inventory."""
    
    def __init__(self):
        self.inventory = {}
        self.reservations = {}
    
    def add_product(self, product_id: str, quantity: int):
        """Add product to inventory."""
        if product_id in self.inventory:
            self.inventory[product_id] += quantity
        else:
            self.inventory[product_id] = quantity
    
    def reserve_product(self, product_id: str, quantity: int, order_id: str) -> bool:
        """
        Reserve product for an order.
        
        BUG: Race condition - two orders can reserve same item
        BUG: No rollback if reservation fails
        """
        if product_id not in self.inventory:
            return False
        
        available = self.inventory[product_id]
        
        # BUG: Check and update are not atomic
        if available >= quantity:
            # Simulate delay where another order could come in
            self.inventory[product_id] -= quantity
            
            # BUG: If this fails, inventory is already decreased
            if order_id not in self.reservations:
                self.reservations[order_id] = []
            
            self.reservations[order_id].append({
                'product_id': product_id,
                'quantity': quantity
            })
            return True
        
        return False
    
    def get_available_quantity(self, product_id: str) -> int:
        """Get available quantity."""
        # BUG: Doesn't account for pending reservations
        return self.inventory.get(product_id, 0)

class OrderProcessor:
    """Process orders with inventory check."""
    
    def __init__(self, inventory_manager: InventoryManager):
        self.inventory = inventory_manager
        self.orders = []
    
    def create_order(self, order_data: Dict) -> Optional[Dict]:
        """
        Create an order.
        
        BUG: Complex validation logic with edge cases
        """
        order_id = order_data.get('order_id')
        items = order_data.get('items', [])
        
        if not order_id or not items:
            return None
        
        # Validate and reserve all items
        reserved_items = []
        
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # BUG: Negative quantity not validated
            if quantity <= 0:
                # BUG: Should rollback previous reservations
                return None
            
            success = self.inventory.reserve_product(
                product_id, quantity, order_id
            )
            
            if not success:
                # BUG: Partial reservation not rolled back
                return None
            
            reserved_items.append(item)
        
        order = {
            'order_id': order_id,
            'items': reserved_items,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        self.orders.append(order)
        return order
    
    def calculate_order_total(self, order: Dict) -> float:
        """
        Calculate order total.
        
        BUG: Floating point precision issues
        BUG: Doesn't handle missing price field
        """
        total = 0.0
        
        for item in order['items']:
            # BUG: Missing price key will crash
            price = item['price']
            quantity = item['quantity']
            
            # BUG: Floating point arithmetic
            total = total + (price * quantity)
        
        # BUG: Discount calculation can result in negative price
        if total > 100:
            discount = total * 0.1
            total = total - discount
        
        # BUG: Rounding issues with currency
        return total

def main():
    """Demonstrate the bugs."""
    
    inventory = InventoryManager()
    processor = OrderProcessor(inventory)
    
    # Setup inventory
    inventory.add_product("BOOK001", 5)
    inventory.add_product("PEN001", 10)
    
    print("Initial inventory:")
    print(f"BOOK001: {inventory.get_available_quantity('BOOK001')}")
    print(f"PEN001: {inventory.get_available_quantity('PEN001')}")
    
    # Order 1: Normal order
    order1_data = {
        'order_id': 'ORDER001',
        'items': [
            {'product_id': 'BOOK001', 'quantity': 2, 'price': 29.99},
            {'product_id': 'PEN001', 'quantity': 5, 'price': 1.99}
        ]
    }
    
    order1 = processor.create_order(order1_data)
    
    if order1:
        total = processor.calculate_order_total(order1)
        print(f"\nOrder 1 created: {order1['order_id']}")
        print(f"Total: ${total}")
    
    # Order 2: Will cause issues
    order2_data = {
        'order_id': 'ORDER002',
        'items': [
            # BUG: This item doesn't have price - will crash
            {'product_id': 'BOOK001', 'quantity': 4}
        ]
    }
    
    order2 = processor.create_order(order2_data)
    
    if order2:
        # This will crash due to missing 'price' key
        total = processor.calculate_order_total(order2)
        print(f"\nOrder 2 created: {order2['order_id']}")
        print(f"Total: ${total}")
    
    # Order 3: Over-booking test
    order3_data = {
        'order_id': 'ORDER003',
        'items': [
            {'product_id': 'BOOK001', 'quantity': 10, 'price': 29.99}  # Only 5 available
        ]
    }
    
    order3 = processor.create_order(order3_data)
    
    if order3:
        print(f"\nOrder 3 created: {order3['order_id']}")
    else:
        print("\nOrder 3 failed - insufficient inventory")
    
    print("\nFinal inventory:")
    print(f"BOOK001: {inventory.get_available_quantity('BOOK001')}")
    print(f"PEN001: {inventory.get_available_quantity('PEN001')}")

if __name__ == "__main__":
    main()