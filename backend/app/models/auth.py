"""Authentication data models."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model."""
    username: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class Token(BaseModel):
    """Access token model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model."""
    username: str
    is_active: bool
    created_at: datetime 