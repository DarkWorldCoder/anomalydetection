from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.responses import create_response
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="1.0") 

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return create_response(message="Backend is healthy")