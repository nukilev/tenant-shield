import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()

class ClauseAnalysis(BaseModel):
    risk_level: str = Field(description="רמת הסיכון של הסעיף לשוכר: 'green', 'yellow', או 'red'")
    explanation: str = Field(description="הסבר קצר, ברור ופשוט בעברית על משמעות הסעיף בשפה יומיומית.")
    alternative_text: str = Field(description="הצעה לנוסח חלופי והוגן שהשוכר יכול להציע למשכיר כדי להגן על עצמו.")

def read_contract_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def analyze_contract_clause(clause_text):
    client = genai.Client()

    system_instruction = (
        "אתה עורך דין מומחה לדיני שכירות בישראל. תפקידך לנתח סעיפים מחוזי שכירות "
        "ולהחזיר פלט בפורמט JSON בלבד. ה-JSON חייב להכיל את המפתחות הבאים:\n"
        "1. 'risk_level': (ערכים אפשריים: 'green', 'yellow', 'red')\n"
        "2. 'explanation': הסבר קצר ופשוט בעברית על משמעות הסעיף לשוכר.\n"
        "3. 'alternative_text': הצעה לנוסח חלופי והוגן שהשוכר יכול להציע למשכיר."
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"נתח את הסעיף הבא:\n\n{clause_text}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_schema=ClauseAnalysis,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return response.text
if __name__ == "__main__":

    contract_text = read_contract_file("contract_sample.txt")

    print("Analyzing contract clause using Gemini...")

    analysis_result_string = analyze_contract_clause(contract_text)

    analysis_json = json.loads(analysis_result_string)

    print(json.dumps(analysis_json, indent=4, ensure_ascii=False))