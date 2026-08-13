# Digital Library Management System

An enterprise grade, fully asynchronous E Library backend API built with **FastAPI**. This system moves beyond standard CRUD operations by integrating advanced Large Language Model (LLM) capabilities, external media fetching, intelligent caching, and strict Role Based Access Control (RBAC).

![img.png](img.png)
## Key Features

* **AI Auto Enrichment:** Add a book using just the Title and ISBN. The system automatically queries an LLM to deduce the author, genre, and description, seamlessly saving the enriched data to the local database.
* **Semantic Search (Ask the AI Librarian):** Users can search the catalog using natural language (e.g., *"I want a fast paced sci fi book about space politics"*). The LLM processes the catalog and returns context aware matches.
* **Smart Recommendations Engine:** Analyzes a user's specific SQL borrowing history and cross references it with current active inventory to generate personalized reading suggestions.
* **OpenLibrary API Integration:** Automatically fetches high resolution book covers and purchase links during book creation, providing rich media for frontend clients.
* **Intelligent Caching:** Expensive external AI calls (like generating book summaries) are cached locally in the database, drastically reducing latency and conserving API quota on subsequent requests.
* **Enterprise Security:** Comprehensive JWT (JSON Web Token) authentication with strict RBAC ensuring secure separation between `MEMBER` and `LIBRARIAN` privileges.
* **Real Time Analytics:** Highly optimized SQL aggregations provide librarians with instant metrics on catalog size, user demographics, active loans, and popular titles.

---

## Technology Stack

* **Framework:** FastAPI (Python 3.10+)
* **Database:** SQLite (via `aiosqlite` for non_blocking I/O)
* **ORM:** SQLAlchemy 2.0 (Asynchronous)
* **Data Validation:** Pydantic v2
* **Security:** Passlib (bcrypt), python jose (JWT)
* **External Integrations:** Userfacet AI API (LLM Gateway), OpenLibrary API, HTTPX

---

## Local Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SFG006/Userfacet_OA_Backend_Shivansh.git
cd Userfacet_OA_Backend_Shivansh

```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Environment Variables

Create a `.env` file in the root directory and add the following keys:

```env
# Security
SECRET_KEY=your_super_secret_cryptographic_key_here

# External AI Integration
MY_API_TOKEN=your_userfacet_ai_token_here

```

### 5. Run the Application

Start the Uvicorn ASGI server. The database and tables will automatically initialize on startup.

```bash
uvicorn app.main:app --reload

```

---

## API Documentation & Usage

Once the server is running, FastAPI automatically generates interactive documentation.

* **Swagger UI:** Navigate to `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)` to test endpoints directly from your browser.
* **ReDoc:** Navigate to `[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)` for alternative, highly detailed API specifications.

### Quick Start Workflow

1. Navigate to `/docs`.
2. Use `POST /auth/register` to create a `LIBRARIAN` account.
3. Click the **Authorize** button at the top right and log in.
4. Use `POST /books/` with just a Title and ISBN to watch the AI and OpenLibrary integrations auto enrich the database.
5. Test the `GET /ai/search` endpoint using natural language.

---

## Project Structure

```text
e-library-management/
├── app/
│   ├── routers/          # Modular API endpoints (auth, books, borrow, ai, analytics)
│   ├── main.py           # FastAPI application instance & lifespan events
│   ├── models.py         # SQLAlchemy ORM models (Database Schema)
│   ├── schemas.py        # Pydantic models for request/response validation
│   ├── database.py       # Async SQLAlchemy engine and session management
│   ├── security.py       # JWT creation, password hashing, and RBAC dependencies
│   ├── ai_service.py     # LLM Gateway communication and prompt engineering
│   └── config.py         # Environment variable management via Pydantic Settings
├── .env                  # Secret keys (Not tracked in version control)
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation

```

---

**Author:** Shivansh Gupta