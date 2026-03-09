from pydantic_settings import BaseSettings
from functools import lru_cache

class InternshipSettings(BaseSettings):
    
    INTERNSHIP_DB_DRIVER: str
    INTERNSHIP_DB_SERVER: str
    INTERNSHIP_DB_NAME: str
    INTERNSHIP_DB_TRUSTED_CONNECTION: str = "yes"
    GEMINI_API_KEY: str
    INTERNSHIP_CHROMA_DB_PATH: str = "./data/chroma_internship"
    MIN_CLUSTERS: int = 5
    MAX_CLUSTERS: int = 15
    N_KEYWORDS: int = 10
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        extra = "ignore"



@lru_cache()
def get_settings() -> InternshipSettings:
    return InternshipSettings()


settings = get_settings()