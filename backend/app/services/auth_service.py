"""Authentication service."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.models.auth import User, UserInDB, TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    def __init__(self):
        """Initialize authentication service."""
        # In production, this would come from a database
        # For now, we'll use the admin user from config
        self.users_db = {
            settings.admin_username: UserInDB(
                username=settings.admin_username,
                hashed_password=self.get_password_hash(settings.admin_password),
                is_active=True,
                created_at=datetime.utcnow()
            )
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username."""
        return self.users_db.get(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with username and password."""
        user = self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            token_data = TokenData(username=username)
            return token_data
        except JWTError:
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token."""
        token_data = self.verify_token(token)
        if token_data is None:
            return None
        
        user = self.get_user(username=token_data.username)
        if user is None:
            return None
        
        return User(
            username=user.username,
            is_active=user.is_active,
            created_at=user.created_at
        )


# Global auth service instance
auth_service = AuthService() 