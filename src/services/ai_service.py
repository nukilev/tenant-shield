from google import genai
from google.genai import types
from src.models.analysis import ContractReport
from google.genai.errors import APIError

def analyze_full_contract(contract_text: str) -> str:
    client = genai.Client()

    system_instruction = (
        "אתה עורך דין מומחה לדיני שכירות ומקרקעין בישראל. תפקידך לסרוק חוזה שכירות שלם, "
        "לזהות את כל הסעיפים המהותיים (במיוחד הבעייתיים או החד-צדדיים), ולנתח אותם עבור השוכר "
        "ביחס לחוק שכירות הוגנת ולסטנדרט המקובל בשוק. עליך להחזיר רשימה מפורטת של הסעיפים הללו."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=ContractReport,  # שימוש ב-Schema של הדוח המלא
        temperature=0.1,  # טמפרטורה נמוכה לעקביות מירבית
    )

    prompt = (
        f"אנא סרוק את חוזה השכירות הבא מתחילתו ועד סופו.חלץ ממנו את הסעיפים החשובים ביותר, "
        f"ונתח כל אחד מהם לפי רמת סיכון (red/yellow/green):\n\n{contract_text}"
    )

    try:
        print("[AI] Analyzing full contract with Gemini 1.5 Pro (Single Shot)...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config,
        )
        return response.text

    except APIError as e:
        if e.code == 503:
            print("[AI] ⚠️ Gemini 1.5 Pro is busy. Switching to Gemini 1.5 Flash for full contract...")
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=config,
            )
            return response.text
        else:
            raise e