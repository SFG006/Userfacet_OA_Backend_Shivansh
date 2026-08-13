import httpx
import json
from fastapi import HTTPException
from app.config import settings


class AIService:
    def __init__(self):
        self.base_url = settings.AI_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {settings.AI_API_TOKEN}",
            "Content-Type": "application/json"
        }

    async def get_usage_quota(self) -> dict:
        """Fetches remaining AI API quota."""
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/v1/usage", headers=self.headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="Failed to fetch AI usage quota")
            return res.json()

    async def generate_book_summary(self, title: str, author: str, description: str) -> dict:
        """Calls Userfacet LLM proxy to generate a structured JSON summary."""
        prompt = f"""
        Analyze the following book and provide a structured JSON response.
        Title: {title}
        Author: {author}
        Description: {description}

        Output ONLY valid JSON matching this schema:
        {{
            "executive_summary": "A concise 2 to 3 sentence overview.",
            "key_takeaways": "Bullet points of key learnings or themes separated by semicolons.",
            "target_audience": "Ideal readers for this book."
        }}
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system",
                 "content": "You are an expert literary critic and librarian assistant. Respond strictly in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(f"{self.base_url}/v1/chat/completions", headers=self.headers, json=payload)

            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=f"LLM Gateway Error: {res.text}")

            data = res.json()
            raw_content = data["choices"][0]["message"]["content"]

            try:
                # Sanitize JSON string if markdown wrappers are present
                clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except Exception:
                return {
                    "executive_summary": raw_content[:250],
                    "key_takeaways": "General overview available.",
                    "target_audience": "General Readers"
                }

    async def generate_recommendations(self, user_history: list, available_books: list) -> list:
        """Use LLM to analyze user reading history and recommend matching catalog books."""
        prompt = f"""
        User's Past Borrowing History: {user_history}
        Available Books in Library: {available_books}

        Based on the user's reading history, select up to 3 books from the Available Books list that best match their preferences.
        Provide a specific reason for each recommendation connecting to their reading habits.

        Output ONLY valid JSON matching this schema:
        [
            {{
                "book_id": 1,
                "title": "Book Title",
                "reason": "1 to 2 sentence explanation of why this book matches their interests."
            }}
        ]
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system",
                 "content": "You are an intelligent library recommendation assistant. Respond strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.4
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(f"{self.base_url}/v1/chat/completions", headers=self.headers, json=payload)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=f"LLM Gateway Error: {res.text}")

            data = res.json()
            raw_content = data["choices"][0]["message"]["content"]
            try:
                clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except Exception:
                return []

    async def enrich_book_metadata(self, title: str) -> dict:
        """Using LLM to auto fill missing author, description, and genre based on the title."""
        prompt = f"""
        I am adding a book titled "{title}" to my library. 
        Identify the most likely author, write a concise 2 sentence description, and determine the main genre.

        Output ONLY valid JSON matching this schema:
        {{
            "author": "Author Name",
            "description": "Short description of the book.",
            "genre": "Main Genre"
        }}
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a global library metadata assistant. Respond strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(f"{self.base_url}/v1/chat/completions", headers=self.headers, json=payload)
            if res.status_code != 200:
                # Fallback if the AI API fails
                return {"author": "Unknown Author", "description": "Description unavailable.", "genre": "Uncategorized"}

            data = res.json()
            raw_content = data["choices"][0]["message"]["content"]
            try:
                clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except Exception:
                return {"author": "Unknown Author", "description": "Description unavailable.", "genre": "Uncategorized"}

    async def semantic_search(self, user_query: str, catalog: list) -> list:
        """Uses LLM to find books in the catalog matching a natural language query."""
        prompt = f"""
        User's Natural Language Search Query: "{user_query}"
        Available Library Catalog: {catalog}

        Act as a semantic search engine. Find up to 3 books from the catalog that best match the vibe, topic, or specific request of the user's query.

        Output ONLY valid JSON matching this schema:
        [
            {{
                "book_id": 1,
                "title": "Book Title",
                "author": "Author Name",
                "match_reason": "1 sentence explanation of why this fits their specific query."
            }}
        ]
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a semantic search AI librarian. Respond strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(f"{self.base_url}/v1/chat/completions", headers=self.headers, json=payload)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=f"LLM Gateway Error: {res.text}")

            data = res.json()
            raw_content = data["choices"][0]["message"]["content"]
            try:
                clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except Exception:
                return []


ai_service = AIService()
