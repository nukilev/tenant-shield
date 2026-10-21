import asyncio
import json
from typing import List
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from src.progress_state import update_progress
from src.services.prompts import SINGLE_CLAUSE_SYSTEM_INSTRUCTION, BATCH_SYSTEM_INSTRUCTION
from src.schemas import LegalAnalysisDetail, BatchClauseAnalysis
from src.services.rag_service import LegalRAGService

rag_service = LegalRAGService()

MODELS_FALLBACK_LIST = [
    "gemini-3.8-flash",
]

async def analyze_clause_with_rag(client: genai.Client, clause_text: str) -> dict:
    """Analyzes a single lease clause (used for the Single Clause tab)."""
    legal_context = await asyncio.to_thread(rag_service.search_relevant_laws, clause_text, 2)

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
                        system_instruction=SINGLE_CLAUSE_SYSTEM_INSTRUCTION,
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
                if e.code == 429:
                    await asyncio.sleep(10 * (attempt + 1))
                else:
                    await asyncio.sleep(2)
                    break

    raise last_error


async def _process_single_batch(
    client: genai.Client, batch_idx: int, total_batches: int, batch_clauses: list[str], progress_counter: dict
) -> list[dict]:
    """Helper function to process a single batch concurrently."""

    print(f"🔍 [Batch {batch_idx}/{total_batches}] Retrieving laws from ChromaDB for {len(batch_clauses)} clauses...")

    rag_tasks = [
        asyncio.to_thread(rag_service.search_relevant_laws, clause, 2)
        for clause in batch_clauses
    ]
    batch_contexts = await asyncio.gather(*rag_tasks)

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

    for model_name in MODELS_FALLBACK_LIST:
        for attempt in range(3):
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=batch_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=BATCH_SYSTEM_INSTRUCTION,
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
                if e.code == 429 or e.code == 503:
                    await asyncio.sleep(3 * (attempt + 1))
                continue
            except Exception as e:
                print(f"❌ [Batch {batch_idx}/{total_batches}] Unexpected error on {model_name}: {str(e)}")
                continue

    progress_counter["completed"] += 1
    completed = progress_counter["completed"]

    update_progress(
        status="processing",
        current_batch=completed,
        total_batches=total_batches,
        message=f"הושלם ניתוח מקבץ {completed} מתוך {total_batches}..."
    )

    batch_results = []
    for idx, clause in enumerate(batch_clauses):
        if batch_parsed and idx < len(batch_parsed):
            batch_results.append({
                "clause_text": clause,
                "analysis": batch_parsed[idx],
                "retrieved_context": batch_contexts[idx],
            })
        else:
            batch_results.append({
                "clause_text": clause,
                "analysis": {
                    "risk": "yellow",
                    "summary": "שגיאה בניתוח סעיף",
                    "legal_reasoning": "תקלה בעיבוד המקבץ מול ה-API.",
                    "recommendation": "מומלץ לבדוק את הסעיף בלשונית 'בדיקת סעיף בודד'.",
                    "cited_laws": "לא זמין",
                },
                "retrieved_context": batch_contexts[idx],
            })

    return batch_results


async def analyze_full_contract(
    client: genai.Client, clauses: list[str], batch_size: int = 10
) -> list[dict]:
    """
    Processes all contract batches in true parallel using asyncio.gather
    for maximum speed now that the paid tier is fully active.
    """
    total_clauses = len(clauses)
    total_batches = (total_clauses + batch_size - 1) // batch_size

    update_progress(
        status="processing",
        current_batch=0,
        total_batches=total_batches,
        message=f"מתחיל ניתוח מקבילי של {total_batches} מקבצים..."
    )

    progress_counter = {"completed": 0}

    print(f"\n🚀 [START] Analyzing contract with TRUE FULL PARALLELISM: {total_clauses} clauses in {total_batches} batches.")

    tasks = [
        _process_single_batch(client, batch_idx, total_batches, clauses[i: i + batch_size], progress_counter)
        for batch_idx, i in enumerate(range(0, total_clauses, batch_size), start=1)
    ]

    batch_results_list = await asyncio.gather(*tasks)

    results = []
    for batch_res in batch_results_list:
        results.extend(batch_res)

    print("🎉 [DONE] Full parallel contract analysis completed!\n")
    return results