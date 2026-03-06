from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import engine, Base
from routes import sms, webhook, settings

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Surge AI SMS Playground")

# Enable CORS for the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all. In production restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Lightweight endpoint for Docker health checks."""
    return {"status": "ok"}

# Include routers
app.include_router(sms.router, tags=["SMS"])
app.include_router(webhook.router, tags=["Webhooks"])
app.include_router(settings.router, tags=["Settings"])
