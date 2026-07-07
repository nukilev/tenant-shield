import re
from typing import List

def split_contract_into_chunks(full_text: str, min_chars: int = 40) -> List[str]:

    raw_paragraphs = re.split(r'\n\s*\n', full_text)

    clean_chunks = []
    for paragraph in raw_paragraphs:
        cleaned = paragraph.strip()

        if len(cleaned) >= min_chars:
            clean_chunks.append(cleaned)

    return clean_chunks