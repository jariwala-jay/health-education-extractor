"""Authentication middleware and dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth_service import auth_service
from app.models.auth import User

# Security scheme for JWT token
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    user = auth_service.get_current_user(credentials.credentials)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get the current active user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Optional authentication dependency (doesn't raise exception if no token)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Optional dependency to get the current user without raising an exception.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        Optional[User]: The authenticated user or None
    """
    if not credentials:
        return None
    
    user = auth_service.get_current_user(credentials.credentials)
    return user 