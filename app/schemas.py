from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import RoleEnum


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[RoleEnum] = RoleEnum.MEMBER


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: RoleEnum

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Book Schemas
class BookCreate(BaseModel):
    title: str
    author: Optional[str] = None
    isbn: str
    genre: Optional[str] = None
    description: Optional[str] = None
    total_copies: int = 1


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    genre: str
    description: str
    total_copies: int
    available_copies: int
    cover_url: Optional[str] = None
    buy_link: Optional[str] = None

    class Config:
        from_attributes = True


# Borrow Schemas
class BorrowResponse(BaseModel):
    id: int
    book_id: int
    borrowed_at: datetime
    due_date: datetime
    is_returned: bool

    class Config:
        from_attributes = True


# AI Schemas
class AISummaryResponse(BaseModel):
    book_id: int
    title: str
    executive_summary: str
    key_takeaways: str
    target_audience: str
    cached: bool


# Recommendation
class BookRecommendationItem(BaseModel):
    book_id: int
    title: str
    reason: str


class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: List[BookRecommendationItem]


# Analytics Schemas
class PopularBookItem(BaseModel):
    book_id: int
    title: str
    author: str
    borrow_count: int


class AnalyticsResponse(BaseModel):
    total_books: int
    total_copies: int
    available_copies: int
    total_users: int
    total_members: int
    total_librarians: int
    total_borrows: int
    active_borrows: int
    popular_books: List[PopularBookItem]


# AISearch schema
class AISearchResult(BaseModel):
    book_id: int
    title: str
    author: str
    match_reason: str


class AISearchResponse(BaseModel):
    query: str
    results: List[AISearchResult]
