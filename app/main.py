from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base

# Import all modular routers to register them with the main application
from app.routers import auth, books, borrow, ai, analytics


# ___ Application Lifespan Management ___
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Handles startup and shutdown events for the application gracefully.
    On startup, it connects to the database engine and automatically creates
    all tables defined in our SQLAlchemy models if they do not already exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # The application runs while yielded

    # Any teardown logic (like closing connection pools) would go here after the yield


# ___ FastAPI Application Instance Setup ___
app = FastAPI(
    title="Digital Library Management System",
    description=
    """
    An enterprise grade Digital Library backend powered by advanced LLM capabilities and external integrations. 

    **Key System Features:**
    *  **Semantic Search & AI Assistants:** Natural language querying and personalized reading recommendations.
    *  **Smart Data Enrichment:** Automated metadata generation and auto tagging via LLM for seamless cataloging.
    *  **External Media Integrations:** Dynamic fetching of high res covers and purchase links via the OpenLibrary API.
    *  **Enterprise Security:** Comprehensive Role Based Access Control (RBAC) and JWT authentication.
    *  **Performance Optimization:** Asynchronous database operations, LLM proxy caching, and platform wide analytics.
    """,
    version="1.0.0",
    lifespan=lifespan  # Attach the lifespan manager defined above
)

# ___ Router Registration ___
# We use APIRouter in separate modules to keep the codebase clean and maintainable.
# Including them here mounts their respective endpoints to the main FastAPI app.
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(borrow.router)
app.include_router(ai.router)
app.include_router(analytics.router)


# ___ System Monitoring ___
@app.get("/health", tags=["System"])
async def health_check():
    """
    Standard Health Check Endpoint.
    """
    return {"status": "ok", "service": "E_library_Core_API"}