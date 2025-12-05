from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Read directly from environment variables with fallback
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        # Only load .env file if it exists (for local development)
        # In production (Vercel), use environment variables directly
        env_file = ".env" if os.path.exists(".env") else None
        case_sensitive = False
        # Explicitly tell Pydantic to read from environment variables
        env_file_encoding = 'utf-8'


# Create settings instance
# This will load from environment variables (Vercel) or .env file (local)
try:
    # Create settings - it will use os.getenv defaults if Pydantic doesn't find them
    settings = Settings()
    
    # Validate that required settings are not empty
    if not settings.supabase_url or not settings.supabase_key or not settings.supabase_service_key:
        missing = []
        if not settings.supabase_url:
            missing.append("SUPABASE_URL")
        if not settings.supabase_key:
            missing.append("SUPABASE_KEY")
        if not settings.supabase_service_key:
            missing.append("SUPABASE_SERVICE_KEY")
        
        error_msg = f"Missing environment variables: {', '.join(missing)}\n\n"
        error_msg += "Please set these in Vercel:\n"
        error_msg += "1. Go to: Vercel Dashboard → Your Project → Settings → Environment Variables\n"
        error_msg += "2. Make sure they're set for 'Production' environment\n"
        error_msg += "3. Redeploy after adding them (important!)\n"
        error_msg += "\nAfter adding variables, you MUST redeploy for them to take effect!"
        raise ValueError(error_msg)
        
except Exception as e:
    # If settings fail to load, provide helpful error message
    error_msg = f"Error loading settings: {e}\n\n"
    error_msg += "Make sure these environment variables are set in Vercel:\n"
    error_msg += "  - SUPABASE_URL\n"
    error_msg += "  - SUPABASE_KEY\n"
    error_msg += "  - SUPABASE_SERVICE_KEY\n"
    error_msg += "\nIMPORTANT: After adding variables, you MUST redeploy!"
    
    # In production, raise the error so it shows in logs
    raise RuntimeError(error_msg) from e

