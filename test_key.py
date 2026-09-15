import os
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)
key = os.getenv("GEMINI_API_KEY")
print(f"בודק מפתח שמתחיל ב: {key[:8]}... ומסתיים ב: ...{key[-4:]}")

client = genai.Client(api_key=key)

try:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="שלום, תענה במילה אחת בלבד: בדיקה"
    )
    print(f"✅ הצלחה! תגובת המודל: {response.text}")
except Exception as e:
    print(f"❌ שגיאה: {e}")