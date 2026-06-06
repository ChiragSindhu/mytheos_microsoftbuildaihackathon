"""
MEDIUM BUG: Index out of range + None handling
Expected to crash with: IndexError and TypeError
"""

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        """Add item to cart."""
        self.items.append(item)
    
    def get_item(self, index):
        """Get item by index."""
        # BUG: No bounds checking
        return self.items[index]
    
    def calculate_discount(self, discount_percent):
        """Calculate discounted total."""
        total = sum(item['price'] for item in self.items)
        
        # BUG: Division by zero when discount is 100%
        discount_multiplier = 100 / (100 - discount_percent)
        
        return total / discount_multiplier

def process_order(cart, user_data):
    """Process an order."""
    # BUG: user_data can be None
    user_name = user_data['name']  # Will crash if user_data is None
    
    # BUG: Accessing index that doesn't exist
    first_item = cart.get_item(0)  # Crashes if cart is empty
    
    print(f"Processing order for {user_name}")
    print(f"First item: {first_item}")
    
    # BUG: 100% discount causes division by zero
    discounted = cart.calculate_discount(100)
    print(f"Discounted total: ${discounted}")

def main():
    cart = ShoppingCart()
    
    # Empty cart - will cause index error
    # cart.add_item({'name': 'Book', 'price': 20})
    
    # None user data - will cause attribute error
    user_data = None
    
    process_order(cart, user_data)

if __name__ == "__main__":
    main()