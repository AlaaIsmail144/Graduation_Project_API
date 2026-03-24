import pyodbc
from contextlib import contextmanager
from typing import Generator
from app.internship.core.config import get_settings

settings = get_settings()

def get_connection_string() -> str:
    
    return (
        f"DRIVER={{{settings.DB_DRIVER}}};"
        f"SERVER={settings.DB_SERVER};"
        f"DATABASE={settings.DB_NAME};"
        f"UID={settings.DB_USER};"
        f"PWD={settings.DB_PASSWORD};"
        f"Encrypt={settings.DB_ENCRYPT};"
        f"TrustServerCertificate={settings.DB_TRUST_SERVER_CERTIFICATE};"
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