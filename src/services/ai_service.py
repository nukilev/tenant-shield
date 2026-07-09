import asyncio
from google import genai
from google.genai import types
from google.genai.errors import APIError
from src.models.analysis import ClauseAnalysis


async def analyze_single_chunk_gemini(sem: asyncio.Semaphore, client: genai.Client, chunk_text: str) -> dict:
    async with sem:
        system_instruction = (
            "אתה עורך דין מומחה לדיני שכירות ומקרקעין בישראל. תפקידך לנתח סעיף מחוזה שכירות "
            "ולהציף סיכונים מהותיים עבור השוכר, תוך השוואה לחוק שכירות הוגנת ולסטנדרט המקובל בשוק."
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

            # השהייה קלה של שנייה וחצי מיד אחרי הקריאה כדי לתת למכסה של גוגל להתאושש
            await asyncio.sleep(1.5)
            return {"original_text": chunk_text, "analysis": response.text}

        except APIError as e:
            # מנגנון הגנה: אם Pro חסום או עמוס (503/429), עוברים מייד ל-Flash האסינכרוני
            if e.code in [429, 503]:
                print(f"  [AI Warning] Gemini Pro rate limit or busy ({e.code}). Switching to Flash for this clause...")
                await asyncio.sleep(3)  # לוקחים נשימה ארוכה יותר
                try:
                    response = await client.aio.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=f"נתח בצורה מעמיקה את הסעיף הבא מהחוזה:\n\n{chunk_text}",
                        config=config,
                    )
                    return {"original_text": chunk_text, "analysis": response.text}
                except Exception as flash_e:
                    return {"original_text": chunk_text, "error": f"Flash fallback failed: {flash_e}"}
            else:
                return {"original_text": chunk_text, "error": str(e)}


async def analyze_all_chunks_parallel(chunks: list) -> list:
    client = genai.Client()

    sem = asyncio.Semaphore(2)

    print(f"[Gemini API] Launching {len(chunks)} tasks with controlled concurrency (Max 2 at a time)...")
    tasks = [analyze_single_chunk_gemini(sem, client, chunk) for chunk in chunks]

    results = await asyncio.gather(*tasks)
    return results