# Digital Library Management System
<p align="left">
  <img src="https://img.shields.io/badge/PYTHON-3.10%2B-FFEA00?style=for-the-badge&logo=python&logoColor=black" alt="Python">
  <img src="https://img.shields.io/badge/FASTAPI-FRAMEWORK-2E7D32?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLALCHEMY-2.0-FF9100?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/PYDANTIC-V2-FF007F?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic">
  <img src="https://img.shields.io/badge/LLM-GPT--4O--MINI-FF1744?style=for-the-badge&logo=openai&logoColor=white" alt="AI Gateway">
  <img src="https://img.shields.io/badge/LICENSE-MIT-7C4DFF?style=for-the-badge&logoColor=white" alt="License">
</p>
Enterprise Grade Asynchronous Backend API built with FastAPI, integrating Large Language Model (LLM) intelligence, dynamic media orchestration, probabilistic machine learning pipelines, and strict Role Based Access Control (RBAC).

###  Backend API  
[![Live API](https://img.shields.io/badge/DIGITAL_LIBRARY_API-OPEN-2563EB?style=for-the-badge&logo=fastapi&logoColor=white)](https://userfacet-oa-backend-shivansh.onrender.com/docs)

![img_1.png](img_1.png)


---


## System Overview

| Specification | Details                                          |
| --- |--------------------------------------------------|
| **Framework** | FastAPI (Python 3.10+)                           |
| **Database Engine** | SQLite via `aiosqlite` (Non_blocking I/O)        |
| **ORM** | SQLAlchemy 2.0 (Asynchronous Session Management) |
| **Validation Layer** | Pydantic v2                                      |
| **Security Architecture** | JWT Bearer Tokens, Passlib (bcrypt), Strict RBAC |
| **AI Integration** | Userfacet LLM Gateway (`gpt-4o-mini`), HTTPX     |

---

## Key Features

* **AI Auto Enrichment:** Add a book using just the Title and ISBN. The system automatically queries an LLM to deduce the author, genre, and description, seamlessly saving the enriched data to the local database.
* **Semantic Search (Ask the AI Librarian):** Users can search the catalog using natural language (e.g., *"I want a fast_paced sci_fi book about space politics"*). The LLM processes the catalog and returns context aware matches.
* **Smart Recommendations Engine:** Analyzes a user's specific SQL borrowing history and cross_references it with current active inventory to generate personalized reading suggestions.
* **Virtual "Debate the Author" Mode:** Users can submit a critique or thesis on any book. The LLM adopts the persona of the author in the first person to defend its creative choices in a real time intellectual debate.
* **Ensemble Learning Spoiler Guard:** Reviews are passed through a two layer classification pipeline (combining fast rule based heuristics with probabilistic LLM analysis) to automatically detect and flag plot spoilers before saving.
* **"What If" Alternate Ending Sandbox:** A creative generative sandbox allowing users to submit counterfactual plot alterations and simulate narrative divergences in the stylistic voice of the author.
* **OpenLibrary API Integration:** Automatically fetches high resolution book covers and purchase links during book creation, providing rich media for frontend clients.
* **Intelligent Caching:** Expensive external AI calls (like generating book summaries) are cached locally in the database, drastically reducing latency and conserving API quota on subsequent requests.
* **Enterprise Security & Integrity:** Comprehensive JWT authentication, strict RBAC (`MEMBER` vs `LIBRARIAN`), and relational integrity checks that protect against orphaned records during catalog deletions.
* **Real Time Analytics:** Highly optimized SQL aggregations provide librarians with instant metrics on catalog size, user demographics, active loans, and popular titles.

---
## API Routes Reference

The FastAPI server exposes the following data streams and management endpoints:

| Endpoint                         | Method | Description                                                                                                       |
|----------------------------------| --- |-------------------------------------------------------------------------------------------------------------------|
| `/auth/register`                 | `POST` | Registers a new user account with secure password hashing and role selection.                                     |
| `/auth/login`                    | `POST` | Authenticates user credentials and returns a secure JWT Bearer token.                                             |
| `/books/`                        | `GET` | Retrieves the active library book inventory and catalog filters.                                                  |
| `/books/`                        | `POST` | Ingests a new book with automated AI metadata enrichment and OpenLibrary media fetching (Librarians only).        |
| `/books/{book_id}`               | `DELETE` | Safely removes a book from the catalog with database referential integrity checks (Librarians only).              |
| `/books/{book_id}/reviews`       | `POST` | Submits a book review processed through an ensemble spoiler detection pipeline.                                   |
| `/borrow/`                       | `POST` | Executes a book checkout transaction, updating inventory counts and generating due dates.                         |
| `/ai/summary/{book_id}`          | `GET` | Returns an AI generated structured executive summary, leveraging local database caching.                          |
| `/ai/recommendations`            | `GET` | Analyzes historical borrowing data via SQL to deliver personalized reading recommendations.                       |
| `/ai/search`                     | `GET` | Processes natural language queries to execute semantic vector context catalog searches.                           |
| `/ai/debate/{book_id}`           | `POST` | Simulates an interactive, first person intellectual debate with the book's author persona.                        |
| `/ai/alternate_ending/{book_id}` | `POST` | Generates a stylistic narrative divergence based on a user submitted counterfactual "What If" prompt.             |
| `/analytics/`                    | `GET` | Returns real time, platform wide metrics on catalog size, user demographics, and loan activity (Librarians only). |

## Assumptions & Technical Notes

* **Environment:** The host machine has Python 3.10 or higher and `pip` installed.
* **Database:** SQLite (via `aiosqlite`) is used for local persistence, requiring no external database server setup (such as PostgreSQL or MySQL).
* **AI Gateway:** An active Userfacet AI API token is provided via the environment variables to support LLM features like summarization, semantic search, and the alternate ending sandbox.
* **Execution Context:** The backend is configured to run locally on `http://127.0.0.1:8000` with auto reload enabled for development.


## Local Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SFG006/Userfacet_OA_Backend_Shivansh.git
cd Userfacet_OA_Backend_Shivansh

```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure Environment Variables

Create a `.env` file in the root configuration directory with the following keys:

```env
SECRET_KEY=your_super_secret_cryptographic_key_here
MY_API_TOKEN=your_userfacet_ai_token_here

```

### 5. Launch the Application Server

Initialize the Uvicorn ASGI server. Database tables and structural relations build automatically on startup.

```bash
uvicorn app.main:app --reload

```

---

## API Documentation & Verification

Interactive documentation interfaces auto-generate upon successful server initialization:

* **Swagger UI:** Accessible at `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`
* **ReDoc Specification:** Accessible at `[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)`

### Quick Start Execution Guide

1. Open the interactive Swagger UI panel at `/docs`.
2. Execute `POST /auth/register` to provision an administrative account with the `LIBRARIAN` role.
3. Authenticate via the native **Authorize** component using your credentials.
4. Test the ingestion pipeline via `POST /books/` using a title and ISBN string to trigger auto enrichment.
5. Probe advanced endpoints including `POST /ai/debate/{book_id}`, `POST /ai/alternate_ending/{book_id}`, or review submission pipelines.

---

## Project Structure

```text
Userfacet_OA_Backend_Shivansh/
├── app/
│   ├── routers/          # Modularized endpoint controllers (auth, books, borrow, ai, analytics)
│   ├── main.py           # Application factory and lifespan event handlers
│   ├── models.py         # Asynchronous SQLAlchemy database schema models
│   ├── schemas.py        # Pydantic data serialization and validation models
│   ├── database.py       # Engine creation and session dependency factories
│   ├── security.py       # Cryptographic utilities, JWT encoding, and RBAC guards
│   ├── ai_service.py     # LLM Gateway client logic and prompt definitions
│   └── config.py         # Pydantic settings management for environment variables
├── .env                  # Local secret keys (Excluded from version control)
├── requirements.txt      # Pinned project dependencies
└── README.md             # System documentation

```

---
<div align="center">
  <sub><i>"A library preserves the thoughts of the past. Intelligent architecture allows them to think for the future."</i></sub>
</div>
