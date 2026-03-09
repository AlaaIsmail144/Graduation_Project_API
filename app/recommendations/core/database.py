import pyodbc
from .config import settings 


class DatabaseManager:
    def __init__(self):
        self.conn_str = self._build_connection_string()
        self._connected = False

    def _build_connection_string(self) -> str:
        if settings.RECOMMENDATION_SQL_USE_WINDOWS_AUTH:
            return (
                'DRIVER={ODBC Driver 17 for SQL Server};'
                f'SERVER={settings.RECOMMENDATION_SQL_SERVER};'
                f'DATABASE={settings.RECOMMENDATION_SQL_DATABASE};'
                'Trusted_Connection=yes;'
            )
        else:
            return (
                'DRIVER={ODBC Driver 17 for SQL Server};'
                f'SERVER={settings.RECOMMENDATION_SQL_SERVER};'
                f'DATABASE={settings.RECOMMENDATION_SQL_DATABASE};'
                f'UID={settings.RECOMMENDATION_SQL_USERNAME};'
                f'PWD={settings.RECOMMENDATION_SQL_PASSWORD};'
            )

    def _test_connection(self):
        try:
            conn = self.get_connection()
            conn.close()
            self._connected = True
        except Exception as e:
            raise Exception(f" Failed to connect to SQL Server: {e}")
   
    def get_connection(self):
        return pyodbc.connect(self.conn_str)
 
    def ensure_connected(self):
        if not self._connected:
            self._test_connection()

try:
    db_manager = DatabaseManager()
except Exception as e:
    print(f" can't initialize database connection on import: {e}")
    db_manager = None