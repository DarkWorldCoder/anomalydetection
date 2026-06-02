from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="Anomaly Detection API", version="1.0") 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, adjust in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "Backend is healthy"}