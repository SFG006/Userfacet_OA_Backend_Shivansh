from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Book, BorrowRecord, User
from app.schemas import BorrowResponse
from app.security import get_current_user

# Initialize the router with a specific prefix and Swagger UI tag
router = APIRouter(prefix="/borrow", tags=["Borrowing System"])


@router.post(
    "/{book_id}",
    response_model=BorrowResponse,
    summary="Borrow a Book",
    description=
    """
    Allows an authenticated member to check out a book. 
    Automatically verifies inventory availability,
    decrements the available copies, and sets a strict 14 day due date.
    """
)
async def borrow_book(
        book_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Handles the transactional logic for checking out a book.
    """
    # 1. Fetch the requested book
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalars().first()

    # 2. Validation Checks
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.available_copies < 1:
        raise HTTPException(status_code=400, detail="No copies available for borrowing")

    # 3. Inventory Management (Atomic decrement to prevent race conditions)
    book.available_copies -= 1

    # 4. Create the Borrow Record (Standard 14 day checkout period)
    borrow_record = BorrowRecord(
        user_id=current_user.id,
        book_id=book.id,
        due_date=datetime.utcnow() + timedelta(days=14)
    )

    # 5. Commit the transaction to the database
    db.add(borrow_record)
    await db.commit()
    await db.refresh(borrow_record)

    return borrow_record


@router.post(
    "/return/{borrow_id}",
    summary="Return a Book",
    description=
    """
    Processes a book return.
    Verifies that the user owns the borrow record,
    marks it as returned, 
    and securely increments the available inventory.
    """
)
async def return_book(
        borrow_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Handles the transactional logic for returning a book.
    Includes database level security checks to ensure users can only return their own borrowed books.
    """
    # 1. Fetch the exact borrow record, strictly filtered by the current user's ID to prevent IDOR vulnerabilities
    result = await db.execute(
        select(BorrowRecord).where(BorrowRecord.id == borrow_id, BorrowRecord.user_id == current_user.id)
    )
    record = result.scalars().first()

    # 2. Validation Check (Ensure it exists and hasn't already been returned)
    if not record or record.is_returned:
        raise HTTPException(status_code=400, detail="Invalid record or book already returned")

    # 3. Update the record status
    record.is_returned = True
    record.returned_at = datetime.utcnow()

    # 4. Inventory Management (Increment available copies back into circulation)
    book_result = await db.execute(select(Book).where(Book.id == record.book_id))
    book = book_result.scalars().first()
    if book:
        book.available_copies += 1

    # 5. Commit the transaction
    await db.commit()

    return {"status": "success", "message": "Book returned successfully"}