from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):

    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_SERVER: str = "db39895.public.databaseasp.net"
    DB_NAME: str = "db39895"
    DB_USER: str = "db39895"
    DB_PASSWORD: str = "sD-8+7Eyq_9S"
    DB_ENCRYPT: str = "yes"
    DB_TRUST_SERVER_CERTIFICATE: str = "yes"
    GEMINI_API_KEY: str = "AIzaSyBcP9rldHcsAjWbDB7Q5nY0qxFlqt50arE"
    CHROMA_DB_PATH: str = "./data/chroma_internship"
    MIN_CLUSTERS: int = 5
    MAX_CLUSTERS: int = 15
    OPTIMAL_CLUSTER_METHOD: str = "auto"
    N_KEYWORDS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore" 


@lru_cache()
def get_settings() -> Settings:
    return Settings()