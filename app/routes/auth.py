from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.schemas import UserRegister, UserLogin, TokenResponse
from app.database import supabase

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """
    Register a new user.
    
    Args:
        user_data: User registration data (email and password)
        
    Returns:
        Access token and user information
    """
    try:
        # Create user with Supabase Auth
        # Set redirect_to for email confirmation callback
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "email_redirect_to": "http://localhost:8000/auth/confirm"
            }
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Get session token
        # Note: If email confirmation is enabled, session will be None
        # until user confirms their email
        session = response.session
        if not session:
            # User created successfully, but email confirmation is required
            # This happens when "Enable email confirmations" is ON in Supabase
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Registration successful! Please check your email to confirm your account before logging in.",
                    "email_confirmed": False,
                    "email": response.user.email,
                    "requires_confirmation": True
                }
            )
        
        return TokenResponse(
            access_token=session.access_token,
            token_type="bearer",
            user={
                "id": response.user.id,
                "email": response.user.email
            }
        )
    except Exception as e:
        error_message = str(e)
        
        # Log the full error for debugging
        print(f"Registration error: {error_message}")
        print(f"Error type: {type(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        
        # Handle Supabase specific errors
        if hasattr(e, 'response'):
            try:
                error_detail = e.response.json() if hasattr(e.response, 'json') else {}
                error_msg = error_detail.get('msg', error_detail.get('message', error_message))
                error_code = error_detail.get('code', None)
                
                # Handle specific Supabase error codes
                if error_code == 'signup_disabled':
                    raise HTTPException(status_code=400, detail="User registration is disabled in Supabase settings.")
                
                if 'already registered' in error_msg.lower() or 'already exists' in error_msg.lower():
                    raise HTTPException(status_code=400, detail="An account with this email already exists. Please log in instead.")
                    
                if 'rate limit' in error_msg.lower() or 'security purposes' in error_msg.lower():
                    # Extract wait time if available
                    import re
                    wait_match = re.search(r'(\d+)\s+seconds?', error_msg)
                    if wait_match:
                        wait_time = wait_match.group(1)
                        raise HTTPException(
                            status_code=429,
                            detail=f"Too many sign-up attempts. Please wait {wait_time} seconds before trying again. This is a security feature to prevent spam."
                        )
                    
                # Use the detailed error message from Supabase
                raise HTTPException(status_code=400, detail=f"Registration failed: {error_msg}")
            except HTTPException:
                raise
            except Exception:
                pass  # Fall through to general error handling
        
        # Handle rate limiting error with better message
        if "security purposes" in error_message or "rate limit" in error_message.lower():
            # Extract wait time if available
            import re
            wait_match = re.search(r'(\d+)\s+seconds?', error_message)
            if wait_match:
                wait_time = wait_match.group(1)
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many sign-up attempts. Please wait {wait_time} seconds before trying again. This is a security feature to prevent spam."
                )
            else:
                raise HTTPException(
                    status_code=429,
                    detail="Too many sign-up attempts. Please wait a minute before trying again. This is a security feature to prevent spam."
                )
        
        # Handle other common errors
        if "already registered" in error_message.lower() or "already exists" in error_message.lower():
            raise HTTPException(status_code=400, detail="An account with this email already exists. Please log in instead.")
        
        if "invalid email" in error_message.lower():
            raise HTTPException(status_code=400, detail="Please enter a valid email address.")
        
        if "password" in error_message.lower() and "weak" in error_message.lower():
            raise HTTPException(status_code=400, detail="Password is too weak. Please use a stronger password (at least 6 characters).")
        
        raise HTTPException(status_code=400, detail=f"Registration failed: {error_message}")


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """
    Login user and return JWT token.
    
    Args:
        user_data: User login credentials (email and password)
        
    Returns:
        Access token and user information
    """
    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return TokenResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            user={
                "id": response.user.id,
                "email": response.user.email
            }
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")


@router.get("/confirm")
async def confirm_email(
    token_hash: str = Query(None, description="Email confirmation token from Supabase"),
    type: str = Query(None, description="Confirmation type"),
    redirect_to: str = Query("http://localhost:5173/login", description="Where to redirect after confirmation")
):
    """
    Handle email confirmation callback from Supabase.
    This endpoint receives the callback from Supabase after user clicks email link.
    
    Note: Supabase email confirmation usually redirects directly to frontend.
    This endpoint can handle manual confirmation if needed.
    """
    try:
        # For email confirmation, Supabase typically handles it client-side
        # If we have tokens, we can verify them
        if token_hash and type:
            # Verify the confirmation token
            response = supabase.auth.verify_otp({
                "token_hash": token_hash,
                "type": type
            })
            
            if response.user and response.session:
                # Email confirmed successfully
                return RedirectResponse(url=f"{redirect_to}?confirmed=true&success=true")
        
        # If no tokens provided, redirect anyway (Supabase may have already confirmed)
        return RedirectResponse(url=f"{redirect_to}?confirmed=true")
    except Exception as e:
        error_message = str(e)
        print(f"Email confirmation error: {error_message}")
        return RedirectResponse(url=f"{redirect_to}?error=confirmation_failed")

