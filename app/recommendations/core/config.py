from pydantic_settings import BaseSettings

class RecommendationSettings(BaseSettings):

    RECOMMENDATION_SQL_SERVER: str
    RECOMMENDATION_SQL_DATABASE: str
    RECOMMENDATION_SQL_USE_WINDOWS_AUTH: bool = True

    VECTOR_STUDENTS_PATH: str = "./data/chroma_students_sql"
    VECTOR_INTERNSHIPS_PATH: str = "./data/chroma_internships_sql"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
   

    API_V2_PREFIX: str = "/api/v2"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
settings = RecommendationSettings()