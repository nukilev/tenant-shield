import io
import re
from pypdf import PdfReader
from docx import Document


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Extracts raw text from uploaded file bytes (supports PDF, DOCX, and TXT)."""
    filename_lower = filename.lower()
    file_stream = io.BytesIO(file_bytes)

    if filename_lower.endswith(".pdf"):
        reader = PdfReader(file_stream)
        return "\n".join([page.extract_text() or "" for page in reader.pages])

    elif filename_lower.endswith(".docx"):
        doc = Document(file_stream)
        return "\n".join([p.text for p in doc.paragraphs if p.text])

    elif filename_lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    raise ValueError("Unsupported file format. Only PDF, DOCX, and TXT are allowed.")


import re


def split_contract_into_clauses(full_text: str) -> list[str]:
    """
    Segments raw contract text into coherent, legally meaningful clauses.
    Handles inline clause numbering, messy PDF line breaks, and Hebrew RTL artifacts.
    """
    if not full_text or not full_text.strip():
        return []

    cleaned_text = re.sub(r"[ \t]+", " ", full_text)
    cleaned_text = re.sub(r"\n\s*\n+", "\n\n", cleaned_text)

    clause_boundary_pattern = re.compile(
        r"(?:\n|\.\s+|;\s+|^)"  
        r"("
        r"(?:(?:סעיף|פרק)\s+)?\d{1,2}(?:\.\d{1,2})?\s*[\.\-\)]\s+"  
        r"|"
        r"(?:(?:סעיף|פרק)\s+)?[א-ת]['״]?\s*[\.\-\)]\s+"  
        r")"
    )

    normalized_text = clause_boundary_pattern.sub(r"\n\n__CLAUSE_START__ \1", cleaned_text)

    raw_clauses = normalized_text.split("__CLAUSE_START__")
    clauses = []
    current_clause = ""

    for chunk in raw_clauses:
        chunk = chunk.strip()
        if not chunk:
            continue

        single_line_chunk = " ".join(chunk.splitlines()).strip()

        if len(single_line_chunk) < 60:
            current_clause = (current_clause + " " + single_line_chunk).strip()
            continue

        if current_clause:
            full_clause = f"{current_clause} {single_line_chunk}".strip()
            clauses.append(full_clause)
            current_clause = ""
        else:
            clauses.append(single_line_chunk)

    if current_clause:
        if clauses:
            clauses[-1] = f"{clauses[-1]} {current_clause}".strip()
        else:
            clauses.append(current_clause)

    if len(clauses) < 2:
        paragraphs = [
            " ".join(p.splitlines()).strip()
            for p in full_text.split("\n\n")
            if len(p.strip()) > 50
        ]
        return paragraphs if paragraphs else [full_text.strip()]

    return clauses