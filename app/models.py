import enum
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, Text, Boolean, Column, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ___ Enums ___
class RoleEnum(str, enum.Enum):
    """
    Defines the allowed user roles for Role Based Access Control (RBAC).
    Inheriting from 'str' ensures the enum is serialized correctly in JSON and the database.
    """
    MEMBER = "MEMBER"
    LIBRARIAN = "LIBRARIAN"


# ___ Database Models ___

class User(Base):
    """
    User account model storing authentication details and role permissions.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Enforces RBAC at the database level using the RoleEnum
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.MEMBER)

    # One to Many relationship: A user can have multiple borrow records
    borrows = relationship("BorrowRecord", back_populates="user")


class Book(Base):
    """
    Core inventory model representing a book in the library.
    Indexed heavily on title, author, isbn, and genre to ensure fast search query performance.
    """
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    author: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    isbn: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    genre: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Inventory tracking
    total_copies: Mapped[int] = mapped_column(Integer, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, default=1)

    # External API Media Integration (OpenLibrary/Google Books)
    cover_url = Column(String, nullable=True)
    buy_link = Column(String, nullable=True)

    # Relationships
    borrows = relationship("BorrowRecord", back_populates="book")
    # One to One relationship: Each book has exactly one AI summary cache to prevent duplicate LLM calls
    summary_cache = relationship("AISummaryCache", back_populates="book", uselist=False)


class BorrowRecord(Base):
    """
    Transactional table handling the checkout lifecycle of a book.
    Acts as an association table between Users and Books, but contains extra metadata (due dates).
    """
    __tablename__ = "borrow_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)

    # Timestamps to track the borrowing window
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    returned_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_returned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Back references to populate the parent objects automatically
    user = relationship("User", back_populates="borrows")
    book = relationship("Book", back_populates="borrows")


class AISummaryCache(Base):
    """
    Performance optimization table.
    Stores the expensive LLM generated summaries so subsequent requests for the same book
    can be served instantly from the local database without hitting the external AI API.
    """
    __tablename__ = "ai_summary_caches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Enforce uniqueness so we don't accidentally cache the same book twice
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), unique=True, nullable=False)

    # Structured JSON response fields stored as discrete text columns
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_takeaways: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Links back to the parent Book model
    book = relationship("Book", back_populates="summary_cache")


# Add Float to your existing sqlalchemy imports:
# from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, Text, Boolean, Column, Float

class Review(Base):
    """
    Stores user generated book reviews.
    Includes ML driven anomaly detection flags to protect readers from plot spoilers.
    """
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=5)

    # Ensemble Learning Outputs
    contains_spoilers: Mapped[bool] = mapped_column(Boolean, default=False)
    spoiler_probability: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)