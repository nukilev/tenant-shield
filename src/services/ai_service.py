import asyncio
import json
from typing import List
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.schemas import LegalAnalysisDetail, BatchClauseAnalysis
from src.services.rag_service import LegalRAGService

rag_service = LegalRAGService()

MODELS_FALLBACK_LIST = [
    "gemini-3.8-flash",
]

async def analyze_clause_with_rag(client: genai.Client, clause_text: str) -> dict:
    """Analyzes a single lease clause (used for the Single Clause tab)."""
    legal_context = rag_service.search_relevant_laws(clause_text, top_k=2)

    system_instruction = (
        "You are an expert Israeli legal advisor specializing in residential lease agreements. "
        "Your primary goal is to protect the tenant.\n"
        "Base your analysis, risk classification, and legal reasoning STRICTLY on the provided "
        "Israeli statutory sections under 'Mandatory Legal Sources'. Do not invent laws.\n\n"
        "Risk Classification Rules:\n"
        "- 'red': The clause contradicts a mandatory statutory provision (חוק קוגנטי) or imposes an explicitly illegal obligation.\n"
        "- 'yellow': The clause is ambiguous, one-sided, borderline, or requires clarification.\n"
        "- 'green': The clause is standard, fair, and fully compliant with Israeli law.\n\n"
        "IMPORTANT: All output text fields (summary, legal_reasoning, recommendation, cited_laws) "
        "MUST be written in clear, natural, and professional Hebrew."
    )

    user_prompt = (
        f"Mandatory Legal Sources:\n{legal_context}\n\n"
        f"---\n"
        f"Lease Clause to Analyze:\n{clause_text}"
    )

    last_error = None
    for model_name in MODELS_FALLBACK_LIST:
        for attempt in range(3):
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=LegalAnalysisDetail,
                    ),
                )
                analysis_data = (
                    response.parsed.model_dump()
                    if getattr(response, "parsed", None)
                    else json.loads(response.text)
                )
                return {
                    "clause_text": clause_text,
                    "analysis": analysis_data,
                    "retrieved_context": legal_context,
                }
            except APIError as e:
                last_error = e
                # If rate-limited (429), wait before retrying
                if e.code == 429:
                    await asyncio.sleep(10 * (attempt + 1))
                else:
                    await asyncio.sleep(2)
                    break

    raise last_error


async def analyze_full_contract(
    client: genai.Client, clauses: list[str], batch_size: int = 10
) -> list[dict]:
    """
    Processes contract clauses in batches (default: 10 clauses per API call)
    to drastically reduce RPM usage and prevent 429 Rate Limit errors.
    """
    results = []
    total_clauses = len(clauses)
    total_batches = (total_clauses + batch_size - 1) // batch_size

    print(f"\n🚀 [START] Analyzing contract: {total_clauses} clauses split into {total_batches} batches.")

    system_instruction = (
        "You are an expert Israeli legal advisor specializing in residential lease agreements. "
        "You will receive a numbered list of contract clauses along with their relevant Israeli statutory sections.\n"
        "Analyze EACH clause in the exact order provided and return a matching list of analyses.\n"
        "Risk Classification Rules:\n"
        "- 'red': Contradicts mandatory law or imposes an illegal obligation.\n"
        "- 'yellow': Ambiguous, one-sided, or requires clarification.\n"
        "- 'green': Standard, fair, and compliant with Israeli law.\n"
        "IMPORTANT: Write all text fields in clear, professional Hebrew."
    )

    # Split clauses into chunks of `batch_size` (e.g., 5 clauses per request)
    for batch_idx, i in enumerate(range(0, total_clauses, batch_size), start=1):
        batch_clauses = clauses[i: i + batch_size]
        print(
            f"🔍 [Batch {batch_idx}/{total_batches}] Retrieving laws from ChromaDB for {len(batch_clauses)} clauses...")

        batch_contexts = [rag_service.search_relevant_laws(c, top_k=2) for c in batch_clauses]

        prompt_parts = []
        for idx, (clause, ctx) in enumerate(zip(batch_clauses, batch_contexts), start=1):
            prompt_parts.append(
                f"=== CLAUSE #{idx} ===\n"
                f"Clause Text: {clause}\n"
                f"Relevant Laws:\n{ctx}\n"
            )

        batch_prompt = (
            f"Analyze the following {len(batch_clauses)} lease clauses and return exactly "
            f"{len(batch_clauses)} analysis objects in the 'analyses' list:\n\n"
            + "\n".join(prompt_parts)
        )

        batch_parsed = None
        last_err_msg = ""

        for model_name in MODELS_FALLBACK_LIST:
            for attempt in range(3):
                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=batch_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.1,
                            response_mime_type="application/json",
                            response_schema=BatchClauseAnalysis,
                        ),
                    )
                    if getattr(response, "parsed", None):
                        batch_parsed = [item.model_dump() for item in response.parsed.analyses]
                    else:
                        raw = json.loads(response.text)
                        batch_parsed = raw.get("analyses", [])

                    print(f"✅ [Batch {batch_idx}/{total_batches}] Successfully analyzed with {model_name}!")
                    break

                except APIError as e:
                    last_err_msg = f"{e.code} {e.status}: {e.message}"
                    print(f"⚠️ [Batch {batch_idx}/{total_batches}] APIError on {model_name} -> {last_err_msg}")

                    if e.code == 429:
                        print("⏳ Rate limit hit (429). Waiting 6 seconds before trying next model...")
                        await asyncio.sleep(6)
                    continue
                except Exception as e:
                    last_err_msg = str(e)
                    print(f"❌ [Batch {batch_idx}/{total_batches}] Unexpected error on {model_name}: {last_err_msg}")
                    continue

        # Map results back to each clause in the batch
        for idx, clause in enumerate(batch_clauses):
            if batch_parsed and idx < len(batch_parsed):
                results.append({
                    "clause_text": clause,
                    "analysis": batch_parsed[idx],
                    "retrieved_context": batch_contexts[idx],
                })
            else:
                results.append({
                    "clause_text": clause,
                    "analysis": {
                        "risk": "yellow",
                        "summary": "שגיאה בניתוח סעיף",
                        "legal_reasoning": "חריגה ממגבלת הקצב של ה-API (429). נסה שוב בעוד דקה.",
                        "recommendation": "מומלץ לבדוק את הסעיף בלשונית 'בדיקת סעיף בודד'.",
                        "cited_laws": "לא זמין",
                    },
                    "retrieved_context": batch_contexts[idx],
                })

        # Small pause between batches
        if batch_idx < total_batches:
            await asyncio.sleep(2)

    print("🎉 [DONE] Full contract analysis completed!\n")
    return results