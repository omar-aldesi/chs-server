import os

from fastapi import FastAPI
from app.routes import router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.models import Base
from app.database import engine


load_dotenv()

app = FastAPI()
app.include_router(router)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=[
        "*"
    ],  # Allows all headers (including Content-Type, Authorization, etc.)
)


@app.get("/")
async def read_root():
    """
    Root endpoint for testing the FastAPI application.
    """
    return {"message": "Hello from FastAPI with PostgreSQL & .env access!"}

@app.get("/config_test")
async def get_config_test():
    """
    Endpoint to test if environment variables are loaded correctly.
    Avoid exposing sensitive information directly.
    """
    return {
        "database_url_prefix": os.getenv("DATABASE_URL").split('://')[0] + "://...", # Mask sensitive part
        "claude_key_status": "Loaded" if os.getenv("CLAUDE_KEY") else "Not Loaded",
        "claude_key_first_chars": os.getenv("CLAUDE_KEY")[:5] + "..." if os.getenv("CLAUDE_KEY") else "N/A"
    }

@app.get("/migrate")
async def migrate_endpoint():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
