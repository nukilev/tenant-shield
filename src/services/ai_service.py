import asyncio
from google import genai
from google.genai import types
from src.models.analysis import ClauseAnalysis
from google.genai.errors import APIError

async def analyze_single_chunk_async(client: genai.Client, chunk_text: str) -> dict:
    system_instruction = (
        "אתה עורך דין מומחה לדיני שכירות ומקרקעין בישראל. תפקידך לנתח סעיף מחוזה שכירות "
        "ולהציף סיכונים עבור השוכר, תוך השוואה לחוק שכירות הוגנת ולסטנדרט המקובל בשוק."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=ClauseAnalysis,
        temperature=0.2,
    )

    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"נתח בצורה מעמיקה את הסעיף הבא מהחוזה:\n\n{chunk_text}",
            config=config,
        )
        return {"original_text": chunk_text, "analysis": response.text}

    except APIError as e:
        if e.code == 503:
            response = await client.aio.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"נתח בצורה מעמיקה את הסעיף הבא מהחוזה:\n\n{chunk_text}",
                config=config,
            )
            return {"original_text": chunk_text, "analysis": response.text}
        else:
            return {"original_text": chunk_text, "error": str(e)}

async def analyze_all_chunks_parallel(chunks: list) -> list:
    client = genai.Client()

    tasks = [analyze_single_chunk_async(client, chunk) for chunk in chunks]

    print(f"[AI] Launching {len(tasks)} parallel analysis tasks...")
    results = await asyncio.gather(*tasks)

    return results