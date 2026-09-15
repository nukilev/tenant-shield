import os
import re
import sys
import time
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from src.services.rag_service import LegalRAGService

FILES_TO_INDEX = [
    {
        "path": os.path.join(BASE_DIR, "data", "legal_corpus", "rental_law"),
        "law_name": "חוק השכירות והשאילה, תשל״א–1971"
    },
    {
        "path": os.path.join(BASE_DIR, "data", "legal_corpus", "contracts_general_law"),
        "law_name": "חוק החוזים (חלק כללי), תשל״ג–1973"
    },
    {
        "path": os.path.join(BASE_DIR, "data", "legal_corpus", "contracts_remedies_law"),
        "law_name": "חוק החוזים (תרופות בשל הפרת חוזה), תשל״א–1970"
    }
]

def parse_markdown_law(file_path: str) -> list[dict]:
    if not os.path.exists(file_path):
        print(f"שגיאה: הקובץ {file_path} לא נמצא.")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"####\s+\[(.*?)\]\s+(.*?)\n(.*?)(?=\n####|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)

    clauses = []
    for match in matches:
        clause_id = match[0].strip()
        clause_title = match[1].strip()
        clause_body = match[2].strip()

        full_text = f"{clause_title}\n{clause_body}"

        clauses.append({
            "id": clause_id,
            "title": clause_title,
            "text": full_text
        })
    return clauses


def run_ingestion():
    rag = LegalRAGService()

    try:
        rag.chroma_client.delete_collection(name="israeli_contract_laws")
        rag.collection = rag.chroma_client.get_or_create_collection(
            name="israeli_contract_laws",
            metadata={"hnsw:space": "cosine"}
        )
        print("נמחק מאגר קודם עם מימדים ישנים.")
    except Exception:
        pass

    print("🚀 מתחיל תהליך אינדוקס החקיקה ל-ChromaDB...")

    total_indexed = 0

    for item in FILES_TO_INDEX:
        file_path = item["path"]
        law_name = item["law_name"]

        print(f"\nקורא את: {law_name} ({file_path})...")
        clauses = parse_markdown_law(file_path)
        if not clauses:
            continue

        rag.upsert_clauses(clauses, law_name)
        total_indexed += len(clauses)
        print(f"  ✓ {len(clauses)} סעיפים אונדקסו בהצלחה!")

    print(f"\n🎉 האינדוקס המקומי הושלם בהצלחה! סה\"כ {total_indexed} סעיפים נשמרו בדיסק.")

if __name__ == "__main__":
    run_ingestion()