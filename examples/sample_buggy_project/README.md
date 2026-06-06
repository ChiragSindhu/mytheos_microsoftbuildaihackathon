# Sample Buggy E-Commerce API

This is a deliberately buggy Flask application for testing MYTHEOS.

## Known Issues

1. **TypeError on /api/users/<id>/orders** - Crashes when user has no orders
2. **Division by zero** - Occurs with 100% discount
3. **KeyError** - Missing query parameters
4. **AttributeError** - Accessing None user object
5. **Index out of bounds** - Slicing with limit > array size

## Running

```bash
pip install flask
python -m src.app