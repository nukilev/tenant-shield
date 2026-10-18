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


def split_contract_into_clauses(full_text: str) -> list[str]:
    """
    Segments a full Hebrew contract text into individual clauses based on common
    numbering patterns (e.g., '1.', '1.1', 'סעיף 2').
    """
    lines = full_text.splitlines()
    clauses = []
    current_clause = []

    # Matches standard numbering at the beginning of a line
    clause_start_pattern = re.compile(r"^(?:סעיף\s+)?(\d+(\.\d+)?)\.?\s+")

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        if clause_start_pattern.match(cleaned_line) and current_clause:
            joined = " ".join(current_clause).strip()
            if len(joined) > 30:
                clauses.append(joined)
            current_clause = [cleaned_line]
        else:
            current_clause.append(cleaned_line)

    if current_clause:
        joined = " ".join(current_clause).strip()
        if len(joined) > 30:
            clauses.append(joined)

    # Fallback: split by double newlines if standard numbering was not detected
    if len(clauses) < 3:
        paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 40]
        return paragraphs if paragraphs else [full_text]

    return clauses