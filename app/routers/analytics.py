from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import Book, BorrowRecord, User, RoleEnum
from app.schemas import AnalyticsResponse, PopularBookItem
from app.security import require_role

# Initialize the router with a specific prefix and Swagger UI tag
router = APIRouter(prefix="/analytics", tags=["Librarian Analytics"])


@router.get(
    "/",
    response_model=AnalyticsResponse,
    summary="Platform Analytics Dashboard",
    description=
    """
    Generates real time, platform wide system metrics. 

    **Security:** This endpoint is strictly protected via RBAC 
    and is only accessible to users with the `LIBRARIAN` role.
    """
)
async def get_platform_analytics(
        db: AsyncSession = Depends(get_db),
        user=Depends(require_role(RoleEnum.LIBRARIAN))
):
    """
    Provides platform wide system metrics for Librarians by executing
    highly optimized SQL aggregation queries.
    """
    # 1. Catalog Metrics
    # Using func.coalesce to safely return 0 instead of None if the database is completely empty
    books_res = await db.execute(select(
        func.count(Book.id),
        func.coalesce(func.sum(Book.total_copies), 0),
        func.coalesce(func.sum(Book.available_copies), 0)
    ))
    total_books, total_copies, available_copies = books_res.one()

    # 2. User Account Metrics
    # Counting total users and filtering by specific RoleEnums to get exact demographics
    users_res = await db.execute(select(
        func.count(User.id),
        func.count(User.id).filter(User.role == RoleEnum.MEMBER),
        func.count(User.id).filter(User.role == RoleEnum.LIBRARIAN)
    ))
    total_users, total_members, total_librarians = users_res.one()

    # 3. Borrowing Workflow Metrics
    # Tracking total historical loans vs. active (unreturned) loans
    borrows_res = await db.execute(select(
        func.count(BorrowRecord.id),
        func.count(BorrowRecord.id).filter(BorrowRecord.is_returned == False)
    ))
    total_borrows, active_borrows = borrows_res.one()

    # 4. Top 3 Most Popular Books (by borrow frequency)
    # Joins the Book and BorrowRecord tables, groups by book, and sorts descending by loan count
    popular_query = (
        select(Book.id, Book.title, Book.author, func.count(BorrowRecord.id).label("borrow_count"))
        .join(BorrowRecord, Book.id == BorrowRecord.book_id)
        .group_by(Book.id)
        .order_by(desc("borrow_count"))
        .limit(3)
    )
    popular_res = await db.execute(popular_query)

    # Map the SQL results into our Pydantic response schema
    popular_books = [
        PopularBookItem(
            book_id=row.id,
            title=row.title,
            author=row.author,
            borrow_count=row.borrow_count
        )
        for row in popular_res.all()
    ]

    return AnalyticsResponse(
        total_books=total_books,
        total_copies=total_copies,
        available_copies=available_copies,
        total_users=total_users,
        total_members=total_members,
        total_librarians=total_librarians,
        total_borrows=total_borrows,
        active_borrows=active_borrows,
        popular_books=popular_books
    )