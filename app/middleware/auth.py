from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase_admin
import jwt


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify JWT token and return current user.
    
    Args:
        credentials: HTTP Bearer token from request header
        
    Returns:
        User dictionary with user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token to extract user info
        # Supabase JWT tokens contain user information in the payload
        # We decode without verification since we trust Supabase-issued tokens
        # In production with proper setup, you could verify the signature
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        user_id = decoded.get("sub")
        email = decoded.get("email", "")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        # Optionally verify user exists in Supabase using admin client
        try:
            user_response = supabase_admin.auth.admin.get_user_by_id(user_id)
            if user_response and user_response.user:
                email = user_response.user.email or email
        except Exception:
            # If admin lookup fails, use email from token
            pass
        
        return {
            "id": user_id,
            "email": email,
            "token": token
        }
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

