import pyodbc
from contextlib import contextmanager
from typing import Generator
from app.internship.core.config import get_settings

settings = get_settings()

def get_connection_string() -> str:
    return (
        f"DRIVER={{{settings.INTERNSHIP_DB_DRIVER}}};" 
        f"SERVER={settings.INTERNSHIP_DB_SERVER};"      
        f"DATABASE={settings.INTERNSHIP_DB_NAME};"    
        f"Trusted_Connection={settings.INTERNSHIP_DB_TRUSTED_CONNECTION};"  
    )

@contextmanager
def get_db_connection() -> Generator[pyodbc.Connection, None, None]:
    conn = None
    try:
        conn = pyodbc.connect(get_connection_string())
        yield conn
    finally:
        if conn:
            conn.close()

def get_db() -> pyodbc.Connection:
    return pyodbc.connect(get_connection_string())