from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
   
    
    # ========== Remote SQL Server Configuration ==========
    RECOMMENDATION_SQL_SERVER: str = "db39895.public.databaseasp.net"
    RECOMMENDATION_SQL_DATABASE: str = "db39895"
    RECOMMENDATION_SQL_USER: str = "db39895"
    RECOMMENDATION_SQL_PASSWORD: str = "sD-8+7Eyq_9S"
    RECOMMENDATION_SQL_USE_WINDOWS_AUTH: bool = False
    RECOMMENDATION_SQL_ENCRYPT: str = "yes"
    RECOMMENDATION_SQL_TRUST_SERVER_CERTIFICATE: str = "yes"
    
    # ========== Vector Database Paths ==========
    VECTOR_STUDENTS_PATH: str = "./data/chroma_students_sql"
    VECTOR_INTERNSHIPS_PATH: str = "./data/chroma_internships_sql"
    
    # ========== Embeddings Settings ==========
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # This tells Pydantic to IGNORE extra variables in .env
        extra = "ignore"  # ← This is the KEY fix!


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_connection_string() -> str:
    """
    Build connection string based on authentication type
    For remote databases, uses SQL Server Authentication
    """
    settings = get_settings()
    
    if settings.RECOMMENDATION_SQL_USE_WINDOWS_AUTH:
        # Windows Authentication (for local development)
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.RECOMMENDATION_SQL_SERVER};"
            f"DATABASE={settings.RECOMMENDATION_SQL_DATABASE};"
            f"Trusted_Connection=yes;"
        )
    else:
        # SQL Server Authentication (for remote databases)
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.RECOMMENDATION_SQL_SERVER};"
            f"DATABASE={settings.RECOMMENDATION_SQL_DATABASE};"
            f"UID={settings.RECOMMENDATION_SQL_USER};"
            f"PWD={settings.RECOMMENDATION_SQL_PASSWORD};"
            f"Encrypt={settings.RECOMMENDATION_SQL_ENCRYPT};"
            f"TrustServerCertificate={settings.RECOMMENDATION_SQL_TRUST_SERVER_CERTIFICATE};"
        )


# Export settings instance for use in other modules
settings = get_settings()