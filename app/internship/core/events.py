
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.internship.core.startup_utils import initialize_internship_system


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("topic modeling syetem is running")
    
    try:
        initialize_internship_system()
        print(" topic modeling ready")

        
    except Exception as e:
        print(f"\n there is an error during topic modeling startup: {e}")
        raise
    
    yield
    
    print("\n shutdown topic modeling")