"""Authentication API endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.auth import Token, User, UserLogin, UserResponse
from app.services.auth_service import auth_service
from app.core.auth_middleware import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint that accepts username and password and returns JWT token.
    
    Args:
        form_data: OAuth2 form data with username and password
        
    Returns:
        Token: JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
async def login_json(user_login: UserLogin):
    """
    Alternative login endpoint that accepts JSON data.
    
    Args:
        user_login: User login data with username and password
        
    Returns:
        Token: JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = auth_service.authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        UserResponse: Current user information
    """
    return UserResponse(
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout endpoint (token invalidation would be handled client-side).
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        dict: Success message
    """
    # In a production system, you might want to blacklist the token
    # For now, we'll just return a success message
    return {"message": "Successfully logged out"}


@router.get("/verify")
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """
    Verify if the current token is valid.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        dict: Token validity status
    """
    return {
        "valid": True,
        "username": current_user.username,
        "message": "Token is valid"
    } 