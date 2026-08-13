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


    async def debate_author(self, title: str, author: str, description: str, user_argument: str) -> str:
        """Instructs the LLM to adopt the persona of the book's author and debate the user."""
        prompt = f"""
        You are {author}, the author of the book '{title}'. 
        Here is a brief description of your work: {description}

        A reader has just presented the following critique or argument regarding your book:
        "{user_argument}"

        Respond directly to the reader in the first person ("I"). 
        Defend your creative choices, counter their argument, or explore their thesis from your unique perspective. 
        Keep the response engaging, intellectual, slightly defensive but polite, and strictly under 150 words.
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a famous author engaging in a lively, intellectual debate with a critical reader."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 250,
            "temperature": 0.8  # Higher temperature for more creative/passionate responses
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(f"{self.base_url}/v1/chat/completions", headers=self.headers, json=payload)

            # Graceful fallback if the API fails
            if res.status_code != 200:
                return "I am currently unavailable for debate. Please write to my publisher."

            data = res.json()
            # This returns standard text, no JSON parsing required
            return data["choices"][0]["message"]["content"]


    async def detect_spoiler(self, title: str, review_text: str) -> dict:
        """
        Ensemble Learning Simulation: Combines a rule based heuristic with an LLM classifier
        to calculate the probability that a text contains plot spoilers.
        """
        # Layer 1: Rule Based Heuristic (Simulated feature extraction)
        suspicious_keywords = ["dies", "ending", "turns out", "killer", "plot twist", "finale", "secret", "revealed",
                               "ghost"]
        keyword_hits = sum(1 for word in suspicious_keywords if word in review_text.lower())
        base_probability = min(keyword_hits * 0.15, 0.45)  # Max 45% probability from heuristics alone

        # Layer 2: LLM Zero Shot Classifier
        prompt = f"""
        Act as a text classification model. Analyze this book review for '{title}'.
        Review: "{review_text}"

        Calculate the probability (between 0.0 and 1.0) that this review reveals critical plot spoilers, twists, or endings.
        Output ONLY valid JSON matching this schema:
        {{
            "llm_probability": 0.85,
            "reason": "1 sentence explanation of why it is or isn't a spoiler."
        }}
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a data classification algorithm. Respond strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.1  # Low temperature for deterministic classification
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(f"{self.base_url}/v1/chat/completions", headers=self.headers, json=payload)

                if res.status_code == 200:
                    data = res.json()
                    raw_content = data["choices"][0]["message"]["content"]
                    clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                    llm_result = json.loads(clean_json)

                    # Ensemble Calculation: Weight the LLM higher (70%) and heuristics lower (30%)
                    final_probability = (llm_result.get("llm_probability", 0.0) * 0.7) + (base_probability * 0.3)

                    return {
                        "is_spoiler": final_probability > 0.75,  # Threshold for flagging
                        "probability": round(final_probability, 2),
                        "reason": llm_result.get("reason", "Analyzed via ensemble pipeline.")
                    }
        except Exception:
            pass

        # Fallback if AI fails: rely entirely on the heuristic layer
        return {
            "is_spoiler": base_probability > 0.4,
            "probability": round(base_probability, 2),
            "reason": "Fallback to heuristic rules."
        }

    async def generate_alternate_ending(self, title: str, author: str, description: str,
                                        counterfactual_prompt: str) -> str:
        """Simulates an alternate narrative ending based on a user provided counterfactual scenario."""
        prompt = f"""
        You are {author}, the author of the book '{title}'.
        Here is the core premise and description of your work: {description}

        A reader has proposed a counterfactual 'What If' scenario for this story:
        "{counterfactual_prompt}"

        Rewrite or simulate how the climax and ending of the story would diverge based on this specific change. 
        Maintain your stylistic voice, narrative tone, and literary depth. Keep the response engaging, dramatic, and strictly under 200 words.
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a master storyteller and novelist simulating creative narrative counterfactuals."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.85  # High temperature for maximum narrative creativity
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(f"{self.base_url}/v1/chat/completions", headers=self.headers, json=payload)

            if res.status_code != 200:
                return "The narrative timeline has collapsed. Unable to simulate alternate ending at this time."

            data = res.json()
            return data["choices"][0]["message"]["content"]


ai_service = AIService()
