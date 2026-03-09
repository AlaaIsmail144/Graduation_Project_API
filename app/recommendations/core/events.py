from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.recommendations.core.startup_utils import build_vector_dbs_if_needed


@asynccontextmanager
async def lifespan(app: FastAPI):
   
    print(" start code of recommendation system")    
    try:
        build_vector_dbs_if_needed()
        from app.recommendations.services.vector_service import vector_service
        vector_service.initialize() 
        from app.recommendations.services.data_service import data_service
        data_service.load_all_data()
    
        print("\n recommendation Engine ready")
        
    except Exception as e:
        print(f"\n error during Recommendation Engine startup: {e}")
        raise
    
    yield
    
    print("\n shutting down Recommendation Engine")