from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, dashboard, detection, model, requests
from app.core.config import settings
from app.core.responses import success_response

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(detection.router)
app.include_router(requests.router)
app.include_router(dashboard.router)
app.include_router(model.router)


@app.get("/health")
async def health_check():
    return success_response(message="Backend is healthy", data={"status": "ok"})
