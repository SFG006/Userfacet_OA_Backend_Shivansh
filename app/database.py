from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# ___ Database Engine Setup ---
# Create an asynchronous engine using the URL from our settings.
# `echo=False` disables SQLAlchemy SQL logging in the console (set to True for debugging).
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# ___ Session Factory ___
# Creates a factory for generating new AsyncSession objects for each request.
# `expire_on_commit=False` is crucial in async SQLAlchemy to prevent detached instance errors
# when accessing object attributes after the session transaction is committed.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ___ ORM Base Class ___
# The modern DeclarativeBase class that all of our database models (like Book, User) will inherit from.
class Base(DeclarativeBase):
    pass

# ___ FastAPI Dependency Injection ___
async def get_db():
    """
    Dependency function to provide a database session for a single request.
    Yields the session to the endpoint, and guarantees the session is securely
    closed (cleaned up) once the HTTP response is sent, preventing memory leaks.
    """
    async with AsyncSessionLocal() as session:
        yield session