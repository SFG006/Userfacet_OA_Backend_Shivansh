from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Book, AISummaryCache, BorrowRecord, User
from app.schemas import AISummaryResponse, RecommendationResponse, AISearchResponse
from app.security import get_current_user
from app.ai_service import ai_service

# Initialize the router with a specific prefix and Swagger UI tag
router = APIRouter(prefix="/ai", tags=["AI Powered Features"])


@router.get(
    "/usage-quota",
    summary="Get AI API Quota",
    description=
    """
    Fetches the live AI API token status from the Userfacet proxy to monitor rate limits.
    """
)
async def get_quota(current_user: User = Depends(get_current_user)):
    """Fetch live AI API token status from the proxy."""
    return await ai_service.get_usage_quota()


@router.get(
    "/summary/{book_id}",
    response_model=AISummaryResponse,
    summary="Get Book Summary (with Caching)",
    description=
    """
    Generates an AI powered summary for a specific book.
    Utilizes local database caching to minimize redundant API calls
    and conserve quota.
    """
)
async def get_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves or generates an AI summary for a book.
    Implements a strict caching layer to optimize external LLM usage.
    """
    # 1. Verify the requested book actually exists in the catalog
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 2. Check Database Cache first (Quota Optimization Layer)
    cache_result = await db.execute(select(AISummaryCache).where(AISummaryCache.book_id == book_id))
    cached_summary = cache_result.scalars().first()

    # If we already generated this summary previously, return it instantly
    if cached_summary:
        return {
            "book_id": book.id,
            "title": book.title,
            "executive_summary": cached_summary.executive_summary,
            "key_takeaways": cached_summary.key_takeaways,
            "target_audience": cached_summary.target_audience,
            "cached": True
        }

    # 3. Cache Miss: Call the Userfacet AI LLM Gateway
    ai_data = await ai_service.generate_book_summary(book.title, book.author, book.description)

    # 4. Save the new generated result to the Database Cache for future users
    new_cache = AISummaryCache(
        book_id=book.id,
        executive_summary=ai_data["executive_summary"],
        key_takeaways=ai_data["key_takeaways"],
        target_audience=ai_data["target_audience"]
    )
    db.add(new_cache)
    await db.commit()

    return {
        "book_id": book.id,
        "title": book.title,
        "executive_summary": ai_data["executive_summary"],
        "key_takeaways": ai_data["key_takeaways"],
        "target_audience": ai_data["target_audience"],
        "cached": False
    }


@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Smart Recommendations Engine",
    description=
    """
    Analyzes the current user's past borrowing history via SQL,
    passes the profile to `gpt-4o-mini`, and 
    returns 3 highly personalized book suggestions from the currently available catalog.
    """
)
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates personalized book recommendations using an LLM
    based on the user's past borrow history and the currently available inventory.
    """
    # 1. Fetch the user's explicit borrowing history to build a reading profile
    history_query = select(Book.title, Book.genre).join(BorrowRecord).where(BorrowRecord.user_id == current_user.id)
    history_res = await db.execute(history_query)
    history = [{"title": row.title, "genre": row.genre} for row in history_res.all()]

    # 2. Fetch all books currently in stock (available_copies > 0)
    books_query = select(Book.id, Book.title, Book.genre, Book.description).where(Book.available_copies > 0)
    books_res = await db.execute(books_query)
    available = [{"id": row.id, "title": row.title, "genre": row.genre, "description": row.description} for row in books_res.all()]

    # Edge case: The library has no books available
    if not available:
        return {"user_id": current_user.id, "recommendations": []}

    # Edge case: If this is a brand new user, return generalized highlights instead of calling the AI
    if not history:
        recommendations = [
            {
                "book_id": b["id"],
                "title": b["title"],
                "reason": "Featured catalog title recommended for new members."
            }
            for b in available[:3]
        ]
        return {"user_id": current_user.id, "recommendations": recommendations}

    # 3. Call the AI Service to map the reading profile against the available catalog
    recommendations_data = await ai_service.generate_recommendations(history, available)
    return {"user_id": current_user.id, "recommendations": recommendations_data}


@router.get(
    "/search",
    response_model=AISearchResponse,
    summary="Semantic Book Search (Ask the AI Librarian)",
    description=
    """
    Search for books using natural language! 
    Tell the AI what kind of vibe, topic, or skill you are looking for,
    and it will find the best matches from the catalog.
    """
)
async def ask_ai_librarian(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Semantic AI search mechanism processing natural language queries.
    """
    # 1. Fetch the entire available catalog to serve as the LLM's context window
    books_query = select(Book.id, Book.title, Book.author, Book.genre, Book.description).where(Book.available_copies > 0)
    books_res = await db.execute(books_query)

    catalog = [
        {
            "id": row.id,
            "title": row.title,
            "author": row.author,
            "genre": row.genre,
            "description": row.description
        }
        for row in books_res.all()
    ]

    # Edge case: Empty library
    if not catalog:
        return {"query": query, "results": []}

    # 2. Pass the user's intent and the full catalog to the AI Service for semantic matching
    search_results = await ai_service.semantic_search(query, catalog)
    return {"query": query, "results": search_results}