import io
import re
from pypdf import PdfReader
from docx import Document

def extract_text_from_file(uploaded_file) -> str:
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text

    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(uploaded_file.read()))
        text = "\n".join([p.text for p in doc.paragraphs if p.text])
        return text

    elif filename.endswith(".txt"):
        return uploaded_file.getvalue().decode("utf-8")

    return ""

def split_contract_into_clauses(full_text: str) -> list[str]:
    """
    מפצל את החוזה למקטעים/סעיפים לפי תבניות מספור נפוצות בחוזים בישראל:
    '1.', 'סעיף 1', '1.1' וכו'.
    """
    lines = full_text.splitlines()
    clauses = []
    current_clause = []

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

    if len(clauses) < 3:
        paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 40]
        return paragraphs if paragraphs else [full_text]

    return clauses