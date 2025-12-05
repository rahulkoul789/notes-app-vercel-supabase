from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Union
from datetime import datetime


class NoteCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None


class NoteResponse(BaseModel):
    id: int  # BIGSERIAL from PostgreSQL will be converted to int
    title: str
    content: str
    image_url: Optional[str] = None
    summary: Optional[str] = None
    user_id: str
    created_at: datetime
    updated_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_id(cls, v):
        """Convert id to int if it's a string or bigint"""
        if v is None:
            return v
        return int(v)

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from string if needed"""
        if isinstance(v, str):
            # Handle ISO format strings from Supabase
            v = v.replace('Z', '+00:00')
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Try alternative parsing
                return datetime.fromisoformat(v.replace('+00:00', ''))
        return v

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

