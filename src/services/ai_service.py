from google import genai
from google.genai import types
from src.models.analysis import ClauseAnalysis  # אימפורט יחסי מהמודל שיצרנו


def analyze_contract_text(contract_text: str) -> str:
    client = genai.Client()

    system_instruction = (
        "אתה עורך דין מומחה לדיני שכירות ומקרקעין בישראל. תפקידך לנתח חוזי שכירות מלאים או סעיפים מתוכם, "
        "ולהציף סיכונים מהותיים עבור השוכר, תוך השוואה לחוק שכירות הוגנת ולסטנדרט המקובל בשוק."
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"נתח בצורה מעמיקה את טקסט החוזה הבא והצף את הסיכונים המרכזיים:\n\n{contract_text}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=ClauseAnalysis,
            temperature=0.2,
        ),
    )

    return response.text