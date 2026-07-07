import re
from typing import List

def split_contract_into_chunks(full_text: str, min_chars: int = 40) -> List[str]:
    if not full_text:
        return []

    pattern = r'\n(?=\d+\.)|\n(?=[\u0590-\u05fe]\.)|\n(?=הואיל\s)|\n\s*\n'

    raw_chunks = re.split(pattern, full_text)

    clean_chunks = []
    for chunk in raw_chunks:
        cleaned = chunk.strip()
        # סינון שורות ריקות או כותרות עמוד קצרות מדי
        if len(cleaned) >= min_chars:
            clean_chunks.append(cleaned)

    if len(clean_chunks) <= 1 and len(full_text) > 200:
        # פיצול כל כמה שורות או לפי מעבר שורה פשוט כדי שלא יישאר גוש אחד
        raw_chunks = full_text.split('\n')
        clean_chunks = []
        current_chunk = ""

        for line in raw_chunks:
            current_chunk += line + "\n"
            # כל 4 שורות נחשיב כצ'אנק נפרד לניתוח
            if len(current_chunk) >= 250:
                clean_chunks.append(current_chunk.strip())
                current_chunk = ""
        if current_chunk.strip():
            clean_chunks.append(current_chunk.strip())

    return clean_chunks