from supabase import create_client, Client
from app.config import settings

# Create Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

# Create Supabase client with service key for admin operations
supabase_admin: Client = create_client(settings.supabase_url, settings.supabase_service_key)


def get_user_supabase_client(user_token: str) -> Client:
    """
    Create a Supabase client with the user's JWT token.
    This allows RLS policies to work correctly by setting auth.uid().
    
    Args:
        user_token: The user's JWT access token
        
    Returns:
        Supabase client configured with the user's token
    """
    # Use service role key but set the Authorization header with user's token
    # This allows RLS to work while still having admin privileges
    from supabase.client import ClientOptions
    
    options = ClientOptions(
        headers={
            "Authorization": f"Bearer {user_token}",
            "apikey": settings.supabase_key
        }
    )
    
    # Use anon key but with user's token in headers for RLS
    client = create_client(settings.supabase_url, settings.supabase_key, options)
    return client

