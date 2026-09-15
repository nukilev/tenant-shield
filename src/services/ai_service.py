import asyncio
from google import genai
from google.genai import types
from google.genai.errors import APIError
from src.models.analysis import ClauseAnalysis
from src.services.rag_service import LegalRAGService

rag_service = LegalRAGService()

async def analyze_clause_with_rag(client: genai.Client, clause_text: str) -> dict:
    legal_context = rag_service.search_relevant_laws(clause_text, top_k=2)

    system_instruction = (
        "אתה מומחה משפטי הבודק חוזי שכירות בישראל. תפקידך להגן על השוכר.\n"
        "עליך לבסס את הניתוח, רמת הסיכון והנימוקים **אך ורק על סעיפי החוק המצורפים תחת 'מקורות חוקיים מחייבים'**.\n\n"
        "כללי סיווג סיכון:\n"
        "- red: הסעיף בחוזה סותר הוראת חוק קוגנטית (שלא ניתן להתנות עליה לרעת השוכר, כמו הגבלת ערובות, חובת תיקון ליקויים, או תנאי ביטול חד-צדדיים), או מטיל חיוב בלתי חוקי במפורש.\n"
        "- yellow: הסעיף מעורפל, גבולי, מאפשר שיקול דעת רחב מדי למשכיר, או דורש הבהרה והגבלה לפי עקרון תום הלב.\n"
        "- green: הסעיף תקין, הוגן, עומד בדרישות החוק המצורפות, או שאין לגביו הוראה מגבילה במקורות.\n\n"
        "הנחיות פלט:\n"
        "החזר אך ורק אובייקט JSON תקין (ללא בלוקי markdown של ```json) במבנה הבא:\n"
        "{\n"
        '  "risk": "green" | "yellow" | "red",\n'
        '  "summary": "סיכום תמציתי של מהות הסעיף במשפט אחד",\n'
        '  "legal_reasoning": "נימוק משפטי המסתמך מפורשות על לשון החוק שסופקה",\n'
        '  "recommendation": "המלצה מעשית לשוכר (או תיקון מוצע לניסוח)",\n'
        '  "cited_laws": "ציטוט קצר או הפניה לסעיף החוק הרלוונטי מתוך המקורות"\n'
        "}"
    )

    user_prompt = (
        f"מקורות חוקיים מחייבים לבדיקה:\n{legal_context}\n\n"
        f"---\n"
        f"סעיף מתוך חוזה השכירות לבדיקה:\n{clause_text}"
    )

    response = await client.aio.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json"
        )
    )

    try:
        analysis_data = json.loads(response.text)
    except Exception:
        analysis_data = {
            "risk": "yellow",
            "summary": "סעיף בחוזה",
            "legal_reasoning": response.text,
            "recommendation": "מומלץ לבדוק את ניסוח הסעיף.",
            "cited_laws": "הסתמכות כללית"
        }

    return {
        "clause_text": clause_text,
        "analysis": analysis_data,
        "retrieved_context": legal_context
    }

async def analyze_full_contract(client: genai.Client, clauses: list[str], progress_callback=None) -> list[dict]:

    results = []
    total = len(clauses)

    for i, clause in enumerate(clauses):
        try:
            res = await analyze_clause_with_rag(client, clause)
            results.append(res)
        except Exception as e:
            results.append({
                "clause_text": clause,
                "analysis": {
                    "risk": "yellow",
                    "summary": "שגיאה בניתוח סעיף",
                    "legal_reasoning": f"לא ניתן היה להשלים את הניתוח: {e}",
                    "recommendation": "בדוק את הסעיף ידנית.",
                    "cited_laws": "אין"
                },
                "retrieved_context": ""
            })

        if progress_callback:
            progress_callback(i + 1, total)

        await asyncio.sleep(0.5)

    return results