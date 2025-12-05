from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas import NoteCreate, NoteUpdate, NoteResponse
from app.database import supabase_admin
from app.middleware.auth import get_current_user
from app.services.ai_service import summarize_text
from datetime import datetime

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(note_data: NoteCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new note.
    
    Args:
        note_data: Note data (title, content, optional image_url)
        current_user: Authenticated user (from dependency)
        
    Returns:
        Created note
    """
    try:
        # Generate summary using AI
        summary = summarize_text(note_data.content)
        
        # Insert note into Supabase
        # Using admin client since we've already validated the user in middleware
        note_dict = {
            "title": note_data.title,
            "content": note_data.content,
            "image_url": note_data.image_url,
            "summary": summary,
            "user_id": current_user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_admin.table("notes").insert(note_dict).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create note")
        
        note = response.data[0]
        
        # Ensure id is an integer (BIGSERIAL might come as string)
        if 'id' in note and note['id'] is not None:
            note['id'] = int(note['id'])
        
        # Parse datetime strings if needed
        if 'created_at' in note and isinstance(note['created_at'], str):
            note['created_at'] = datetime.fromisoformat(note['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in note and isinstance(note['updated_at'], str):
            note['updated_at'] = datetime.fromisoformat(note['updated_at'].replace('Z', '+00:00'))
        
        return NoteResponse(**note)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create note: {str(e)}")


@router.get("", response_model=List[NoteResponse])
async def get_notes(current_user: dict = Depends(get_current_user)):
    """
    Get all notes for the current user.
    
    Args:
        current_user: Authenticated user (from dependency)
        
    Returns:
        List of user's notes
    """
    try:
        # Using admin client since we've already validated the user in middleware
        response = supabase_admin.table("notes").select("*").eq("user_id", current_user["id"]).order("created_at", desc=True).execute()
        
        # Convert data types for each note
        notes = []
        for note in response.data:
            # Only convert id if it's actually a number (not a UUID)
            if 'id' in note and note['id'] is not None:
                try:
                    # Check if it's a UUID (contains hyphens) - if so, skip conversion
                    if isinstance(note['id'], str) and '-' in note['id']:
                        # This shouldn't happen - id should be numeric
                        print(f"Warning: id appears to be a UUID: {note['id']}, skipping conversion")
                    elif isinstance(note['id'], str) and note['id'].isdigit():
                        note['id'] = int(note['id'])
                    elif isinstance(note['id'], (int, float)):
                        note['id'] = int(note['id'])
                except (ValueError, TypeError) as e:
                    # If conversion fails, log the error
                    print(f"Error converting id to int: {note.get('id')}, error: {e}")
                    raise HTTPException(status_code=500, detail=f"Invalid note id format: {note.get('id')}")
            
            # Parse datetime strings
            if 'created_at' in note and isinstance(note['created_at'], str):
                try:
                    note['created_at'] = datetime.fromisoformat(note['created_at'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass  # Keep as string if parsing fails
            
            if 'updated_at' in note and isinstance(note['updated_at'], str):
                try:
                    note['updated_at'] = datetime.fromisoformat(note['updated_at'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass  # Keep as string if parsing fails
            
            notes.append(NoteResponse(**note))
        
        return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notes: {str(e)}")


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get a specific note by ID.
    
    Args:
        note_id: Note ID
        current_user: Authenticated user (from dependency)
        
    Returns:
        Note details
    """
    try:
        # Using admin client since we've already validated the user in middleware
        response = supabase_admin.table("notes").select("*").eq("id", note_id).eq("user_id", current_user["id"]).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")
        
        note = response.data[0]
        # Convert data types
        if 'id' in note and note['id'] is not None:
            note['id'] = int(note['id'])
        if 'created_at' in note and isinstance(note['created_at'], str):
            note['created_at'] = datetime.fromisoformat(note['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in note and isinstance(note['updated_at'], str):
            note['updated_at'] = datetime.fromisoformat(note['updated_at'].replace('Z', '+00:00'))
        
        return NoteResponse(**note)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch note: {str(e)}")


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a note.
    
    Args:
        note_id: Note ID to delete
        current_user: Authenticated user (from dependency)
    """
    try:
        # First verify the note belongs to the user
        # Using admin client since we've already validated the user in middleware
        response = supabase_admin.table("notes").select("id").eq("id", note_id).eq("user_id", current_user["id"]).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # Delete the note
        supabase_admin.table("notes").delete().eq("id", note_id).eq("user_id", current_user["id"]).execute()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")


@router.post("/{note_id}/summarize", response_model=NoteResponse)
async def summarize_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """
    Generate or regenerate summary for a note.
    
    Args:
        note_id: Note ID to summarize
        current_user: Authenticated user (from dependency)
        
    Returns:
        Updated note with summary
    """
    try:
        # Using admin client since we've already validated the user in middleware
        # Get the note
        response = supabase_admin.table("notes").select("*").eq("id", note_id).eq("user_id", current_user["id"]).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")
        
        note = response.data[0]
        
        # Generate summary
        summary = summarize_text(note["content"])
        
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary. Check OpenAI API key.")
        
        # Update note with summary
        update_response = supabase_admin.table("notes").update({
            "summary": summary,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", note_id).eq("user_id", current_user["id"]).execute()
        
        if not update_response.data:
            raise HTTPException(status_code=400, detail="Failed to update note")
        
        updated_note = update_response.data[0]
        # Convert data types
        if 'id' in updated_note and updated_note['id'] is not None:
            updated_note['id'] = int(updated_note['id'])
        if 'created_at' in updated_note and isinstance(updated_note['created_at'], str):
            updated_note['created_at'] = datetime.fromisoformat(updated_note['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in updated_note and isinstance(updated_note['updated_at'], str):
            updated_note['updated_at'] = datetime.fromisoformat(updated_note['updated_at'].replace('Z', '+00:00'))
        
        return NoteResponse(**updated_note)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize note: {str(e)}")

