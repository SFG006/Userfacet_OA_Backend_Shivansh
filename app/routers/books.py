from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.models import Book, RoleEnum, BorrowRecord
from app.schemas import BookCreate, BookResponse
from app.security import require_role, get_current_user
from app.ai_service import ai_service
from app.models import Review ,User
from app.schemas import ReviewCreate, ReviewResponse
import httpx

# Initialize the router with a specific prefix and Swagger UI tag
router = APIRouter(prefix="/books", tags=["Books Management"])


# ___ External API Integrations ___
async def fetch_openlibrary_media(isbn: str):
    """
    Fetches high resolution cover images and book links using the free OpenLibrary API.
    Fails gracefully (returns None) if the external API times out or the book isn't found,
    ensuring our core database transaction still succeeds.
    """
    # Clean the ISBN of hyphens to ensure maximum compatibility with OpenLibrary's index
    clean_isbn = isbn.replace("-", "").strip()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # OpenLibrary API endpoint for strict ISBN lookup
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=data"
            res = await client.get(url)

            if res.status_code == 200:
                data = res.json()
                key = f"ISBN:{clean_isbn}"

                # Check if the exact book key was found in their database response
                if key in data:
                    book_data = data[key]

                    # Grab the large or medium cover image if available
                    cover = None
                    if "cover" in book_data:
                        cover = book_data["cover"].get("large") or book_data["cover"].get("medium")

                    # Grab the official OpenLibrary URL for the book
                    buy = book_data.get("url")

                    return cover, buy
    except Exception:
        # Silently catch network errors so the main book creation process isn't interrupted
        pass

    return None, None


# ___ Endpoints ___
@router.post(
    "/",
    response_model=BookResponse,
    status_code=201,
    summary="Add a Book (AI Auto Enrichment Enabled)",
    description=
    """
    Adds a new book to the library inventory. 
    
    ** AI & External API Integration:**
    Provide just the `title` and `isbn`, and the backend handles the rest automatically:
    
    1. **AI Enrichment:** The LLM deduces the author, genre, and writes a short description.
    2. **OpenLibrary Fetch:** The system fetches the official book cover and a purchase link.
    3. **Database Insertion:** Saves the completely enriched record to the local library database.
    """
)
async def add_book(
        book_in: BookCreate,
        db: AsyncSession = Depends(get_db),
        user=Depends(require_role(RoleEnum.LIBRARIAN))
):
    """
    Creates a new book record. Strictly protected by RBAC (Librarians only).
    """
    # 1. Enforce unique ISBNs at the application level
    result = await db.execute(select(Book).where(Book.isbn == book_in.isbn))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")

    # Extract current values from the incoming request payload
    author_val = book_in.author
    genre_val = book_in.genre
    desc_val = book_in.description

    # 2. AI DATA ENRICHMENT LOGIC
    # If the user left core metadata fields blank, trigger the LLM to research and fill them in
    if not author_val or not genre_val or not desc_val:
        ai_data = await ai_service.enrich_book_metadata(book_in.title)

        # Retain user provided values if they exist, otherwise use the AI generated fallbacks
        author_val = author_val or ai_data.get("author", "Unknown Author")
        genre_val = genre_val or ai_data.get("genre", "General")
        desc_val = desc_val or ai_data.get("description", "No description available.")

    # 3. EXTERNAL API MEDIA FETCH
    # Pass the ISBN to OpenLibrary to grab rich media for the frontend
    cover_url, buy_link = await fetch_openlibrary_media(book_in.isbn)

    # 4. Construct the final ORM model and save to the database
    book = Book(
        title=book_in.title,
        author=author_val,
        isbn=book_in.isbn,
        genre=genre_val,
        description=desc_val,
        total_copies=book_in.total_copies,
        available_copies=book_in.total_copies,
        cover_url=cover_url,
        buy_link=buy_link
    )

    db.add(book)
    await db.commit()
    await db.refresh(book)

    return book


@router.get(
    "/",
    response_model=List[BookResponse],
    summary=" List & Search Books",
    description=
    """
    Browse the library catalog using dynamic SQL filtering.
    
    * **Search:** Performs a case-insensitive `ILIKE` search across both the Book Title and Author.
    * **Genre:** Filters by a specific genre category.
    * **Availability:** Toggle `available_only` to hide books that are currently out of stock.
    """
)
async def list_books(
        genre: Optional[str] = None,
        search: Optional[str] = None,
        available_only: bool = False,
        db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a list of books based on dynamic query parameters.
    Builds the SQLAlchemy query conditionally based on what the user provided.
    """
    query = select(Book)

    # Apply genre filter if provided (case insensitive)
    if genre:
        query = query.where(Book.genre.ilike(f"%{genre}%"))

    # Apply global text search across title OR author
    if search:
        query = query.where(
            (Book.title.ilike(f"%{search}%")) | (Book.author.ilike(f"%{search}%"))
        )

    # Filter out books with 0 available copies
    if available_only:
        query = query.where(Book.available_copies > 0)

    # Execute the dynamically built query
    result = await db.execute(query)

    return result.scalars().all()


@router.post(
    "/{book_id}/reviews",
    response_model=ReviewResponse,
    summary="Submit Review (Ensemble Spoiler Guard)",
    description=
    """
    Submits a review and passes the text through a 2 layer ML classification pipeline
    to automatically detect and flag plot spoilers.
    """
)
async def add_review(
        book_id: int,
        review_in: ReviewCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Evaluates review text for spoilers before saving it to the database.
    """
    # 1. Fetch the book to get context for the AI
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 2. Run the text through the AI Service Ensemble Pipeline
    spoiler_analysis = await ai_service.detect_spoiler(title=book.title, review_text=review_in.content)

    # 3. Create the review record with the calculated probabilities
    new_review = Review(
        book_id=book.id,
        user_id=current_user.id,
        content=review_in.content,
        rating=review_in.rating,
        contains_spoilers=spoiler_analysis["is_spoiler"],
        spoiler_probability=spoiler_analysis["probability"]
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    return new_review


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Book",
    description=
    """
    Removes a book from the library catalog. 

    **Enterprise Safeguard:** This endpoint actively checks the `BorrowRecord` table.
    If any user currently has this book checked out, 
    the deletion is blocked to protect database relational integrity.
    """
)
async def delete_book(
        book_id: int,
        db: AsyncSession = Depends(get_db),
        user=Depends(require_role(RoleEnum.LIBRARIAN))
):
    """
    Safely deletes a book from the catalog, ensuring no active loans are orphaned.
    Strictly protected by RBAC (Librarians only).
    """
    # 1. Verify the book actually exists
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalars().first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 2. Referential Integrity Check: Are there active, unreturned borrows?
    active_borrows_query = select(BorrowRecord).where(
        BorrowRecord.book_id == book_id,
        BorrowRecord.is_returned == False
    )
    active_borrows_result = await db.execute(active_borrows_query)

    if active_borrows_result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete book: Copies are currently checked out by users."
        )

    # 3. Safe Deletion
    await db.delete(book)
    await db.commit()

    # 204 No Content responses should not return a body
    return None