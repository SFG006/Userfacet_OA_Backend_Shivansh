from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models import User, RoleEnum

# ___ Security Configurations ___
# Initialize Passlib context for securely hashing passwords using the bcrypt algorithm.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Tells FastAPI where the client can send a username and password to get a token.
# This powers the "Authorize" button in the Swagger UI.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ___ Password Utilities ___
def verify_password(plain_password, hashed_password):
    """Verifies that a plain text password matches the hashed version in the database."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Generates a secure bcrypt hash for a new user's password."""
    return pwd_context.hash(password)


# ___ JWT (JSON Web Token) Management ___
def create_access_token(data: dict):
    """
    Creates a secure, signed JWT for user sessions.
    Embeds the user's email as the subject ('sub') and sets a strict expiration time.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Sign the token using the secret key and HS256 algorithm to prevent tampering
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ___ Authentication Dependencies ___
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    Dependency to validate the JWT token from the incoming request header.
    If the token is valid, it extracts the email, queries the database, and returns the User object.
    Raises a 401 Unauthorized error if the token is expired, invalid, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token securely
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        # Catches expired or cryptographically invalid tokens
        raise credentials_exception

    # Async database lookup to ensure the user still exists in the system
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


# ___ Authorization (RBAC) Dependency ___
def require_role(required_role: RoleEnum):
    """
    Factory function for Role Based Access Control (RBAC).
    Returns a dependency function that checks if the current user has the required role.
    LIBRARIANs are treated as superusers and bypass all role restrictions.
    """

    def role_checker(user: User = Depends(get_current_user)):
        # If the user doesn't have the explicit role AND isn't a Librarian, block them.
        if user.role != required_role and user.role != RoleEnum.LIBRARIAN:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user

    return role_checker