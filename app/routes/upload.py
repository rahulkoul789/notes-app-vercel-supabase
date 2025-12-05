from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.database import supabase, supabase_admin
from app.middleware.auth import get_current_user
import uuid
from typing import Optional

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload an image file to Supabase Storage.
    
    Args:
        file: Image file to upload
        current_user: Authenticated user (from dependency)
        
    Returns:
        URL of the uploaded image
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB"
        )
    
    try:
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{current_user['id']}/{uuid.uuid4()}.{file_extension}"
        
        # Upload to Supabase Storage
        # Using admin client to bypass RLS policies
        storage = supabase_admin.storage.from_("note-images")
        
        # Upload file (Supabase Python client returns a StorageFileApiResponse object)
        upload_response = storage.upload(
            unique_filename,
            file_content,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
        
        # Check for errors in upload response
        # The Supabase client might return a dict with 'error' key or raise an exception
        if isinstance(upload_response, dict):
            if upload_response.get('error'):
                error_data = upload_response.get('error', {})
                if isinstance(error_data, dict):
                    error_msg = error_data.get('message', str(error_data))
                else:
                    error_msg = str(error_data)
                raise HTTPException(status_code=500, detail=f"Failed to upload image: {error_msg}")
        elif hasattr(upload_response, 'error') and upload_response.error:
            error_msg = str(upload_response.error)
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {error_msg}")
        
        # Get public URL
        # The get_public_url method returns a string URL
        public_url_response = storage.get_public_url(unique_filename)
        
        # Handle different response formats from Supabase
        if isinstance(public_url_response, dict):
            url = public_url_response.get('publicUrl') or public_url_response.get('url') or str(public_url_response)
        elif isinstance(public_url_response, str):
            url = public_url_response
        else:
            # Fallback: construct URL manually
            from app.config import settings
            url = f"{settings.supabase_url}/storage/v1/object/public/note-images/{unique_filename}"
        
        # Ensure we have a valid URL
        if not url or url.startswith('{'):
            from app.config import settings
            url = f"{settings.supabase_url}/storage/v1/object/public/note-images/{unique_filename}"
        
        return JSONResponse(content={
            "url": url,
            "filename": unique_filename
        })
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Upload error: {str(e)}")
        print(f"Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}. Make sure the 'note-images' bucket exists in Supabase Storage and is set to public.")

