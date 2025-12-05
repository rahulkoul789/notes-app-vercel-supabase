from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, notes, upload

app = FastAPI(
    title="Notes App API",
    description="A notes app with authentication, file storage, and AI summarization",
    version="1.0.0"
)

# Configure CORS
# Allow localhost for development and environment variable for production
import os
cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
# Add production frontend URL from environment variable if set
if os.getenv("FRONTEND_URL"):
    cors_origins.append(os.getenv("FRONTEND_URL"))
# Add Vercel URLs automatically
if os.getenv("VERCEL_URL"):
    cors_origins.append(f"https://{os.getenv('VERCEL_URL')}")
# In production on Vercel, allow all origins for simplicity
if os.getenv("VERCEL"):
    cors_origins = ["*"]  # Allow all in Vercel production

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(upload.router)


@app.get("/")
async def root():
    return {"message": "Notes App API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

