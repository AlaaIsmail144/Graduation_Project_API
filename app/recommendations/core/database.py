import pyodbc
from typing import Optional
from .config import settings, get_connection_string

class DatabaseManager:

    def __init__(self):
        self.connection_string = get_connection_string()
        self._connection: Optional[pyodbc.Connection] = None
    
    def get_connection(self) -> pyodbc.Connection:
        try:
            if self._connection is None or self._connection.closed:
                self._connection = pyodbc.connect(self.connection_string)
            return self._connection
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            print(f"Connection string (without password): {self.connection_string.replace(settings.RECOMMENDATION_SQL_PASSWORD, '***')}")
            raise
    
    def close(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None


# Initialize db_manager on module import
try:
    db_manager = DatabaseManager()
    print("✅ DatabaseManager initialized successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize database connection on import: {e}")
    db_manager = None  # Will be initialized later if needed