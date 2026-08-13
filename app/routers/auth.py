from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.security import get_password_hash, verify_password, create_access_token

# Initialize the router with a specific prefix and Swagger UI tag
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description=
    """
    Creates a new user account with securely hashed passwords.
    Allows assigning either `MEMBER` or `LIBRARIAN` roles.
    """
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user in the database.
    Checks for email collisions and hashes the password before saving.
    """
    # 1. Check if the email is already in use
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Create the new user with a securely hashed password
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
    )

    # 3. Save to the database
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login / Obtain Token",
    description=
    """
    Authenticates a user and returns a standard JWT Bearer token. 

    **Note:** This endpoint natively connects to the green `Authorize` button 
    at the top of the Swagger UI!
    """
)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Authenticates user credentials and issues a JWT access token.
    Uses FastAPI's built in OAuth2PasswordRequestForm to seamlessly integrate with Swagger UI.
    """
    # 1. Fetch the user by email (OAuth2 standard uses 'username' for the field name)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    # 2. Verify the user exists AND the password matches the hash
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # 3. Generate the JWT token embedded with the user's email
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}