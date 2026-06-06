"""User model - Contains data access bugs."""
from typing import Optional

class User:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """
        Get user by ID.
        
        BUG: Returns None for non-existent users, but calling code
        doesn't check for None before accessing attributes.
        """
        # Mock database
        users = {
            100: User(100, 'John Doe', 'john@example.com'),
            101: User(101, 'Jane Smith', 'jane@example.com'),
        }
        
        # BUG: Should raise exception for invalid user_id
        return users.get(user_id)