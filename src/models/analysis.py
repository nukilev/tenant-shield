from pydantic import BaseModel, Field
from typing import List

class ClauseAnalysis(BaseModel):
    clause_title: str = Field(description="כותרת קצרה או נושא הסעיף (למשל: 'תיקונים בדירה', 'ערבויות', 'פינוי מוקדם')")
    original_text: str = Field(description="הציטוט המדויק או תמצית הסעיף המקורי מתוך החוזה כפי שהופיע בטקסט.")
    risk_level: str = Field(description="רמת הסיכון לשוכר: 'green', 'yellow', או 'red'")
    explanation: str = Field(description="הסבר קצר ופשוט בעברית יומיומית על משמעות הסעיף והסיכון שבו.")
    alternative_text: str = Field(description="נוסח חלופי והוגן שהשוכר יכול להציע למשכיר (רק עבור סעיפי red ו-yellow).")

class ContractReport(BaseModel):
    analyzed_clauses: List[ClauseAnalysis] = Field(description="רשימה של כל הסעיפים החשובים או הבעייתיים שנמצאו בחוזה.")