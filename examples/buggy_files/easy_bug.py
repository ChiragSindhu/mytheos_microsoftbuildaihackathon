"""
EASY BUG: Simple type error
Expected to crash with: TypeError: unsupported operand type(s)
"""

def calculate_total(prices):
    """Calculate total price."""
    total = 0
    for price in prices:
        total = total + price
    return total

def main():
    # BUG: One price is a string instead of number
    prices = [10, 20, "30", 40]
    
    total = calculate_total(prices)
    print(f"Total: ${total}")

if __name__ == "__main__":
    main()