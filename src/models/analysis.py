from pydantic import BaseModel, Field

class ClauseAnalysis(BaseModel):
    risk_level: str = Field(description="רמת הסיכון של הסעיף לשוכר: 'green', 'yellow', או 'red'")
    explanation: str = Field(description="הסבר קצר, ברור ופשוט בעברית על משמעות הסעיף בשפה יומיומית.")
    alternative_text: str = Field(description="הצעה לנוסח חלופי והוגן שהשוכר יכול להציע למשכיר כדי להגן על עצמו.")