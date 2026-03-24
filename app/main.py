from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from contextlib import asynccontextmanager

# internship system imports
from app.internship.api.topics import router as topics_router
from app.internship.api.assignments import router as assignments_router
from app.internship.core.events import lifespan as internship_lifespan

# recommendation engine imports
from app.recommendations.api.routes.recommendations import router as recommendations_router
from app.recommendations.api.routes.search import router as search_router
from app.recommendations.api.routes.sync import router as sync_router
from app.recommendations.core.events import lifespan as rec_lifespan


@asynccontextmanager
async def unified_lifespan(app: FastAPI):
    print(" start system ")
    
    async with rec_lifespan(app):
        async with internship_lifespan(app):
            print(f" Documentation: http://localhost:8001/docs")   
            yield
    
    print(" Shutting down Unified API System...")


app = FastAPI(
    title=" My Integrated API System",
    version="2.0.0",
    description="Combined Internship Topic Modeling & Recommendation Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=unified_lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# include routers 

app.include_router(
    topics_router,
    prefix="/api/v1/topics",
    tags=[" Topics"]
)

app.include_router(
    assignments_router,
    prefix="/api/v1/assignments",
    tags=[" Assignments"]
)

app.include_router(
    recommendations_router,
    prefix="/api/v2/recommendations",
    tags=[" Recommendations"]
)

app.include_router(
    search_router,
    prefix="/api/v2/search",
    tags=[" Search"]
)

app.include_router(
    sync_router,
    prefix="/api/v2/sync",
    tags=[" Sync"]
)


# root endpoints 
@app.get("/", tags=[" Home"])
async def root():
    return {
        "message": " My API integration",
        "version": "2.0.0",
        "services": {
            "internship_system": {
                "version": "1.0.0",
                "description": "Topic Modeling & Assignment System",
                "endpoints": {
                    "topics": "/api/v1/topics",
                    "assignments": "/api/v1/assignments"
                }
            },
            "recommendation_engine": {
                "version": "1.0.0",
                "description": "Personalized Recommendation System",
                "endpoints": {
                    "recommendations": "/api/v2/recommendations",
                    "search": "/api/v2/search",
                    "sync": "/api/v2/sync"
                }
            }
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health", tags=[" Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "internship_system": " operational",
            "recommendation_engine": " operational"
        }
    }


# global exception handler 
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "path": str(request.url.path)
        }
    )


# run server 
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
