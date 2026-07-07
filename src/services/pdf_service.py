import os
from pypdf import PdfReader


def read_pdf_contract(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"הקובץ {file_path} לא נמצא בתיקיית הפרויקט!")

    reader = PdfReader(file_path)
    full_text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

    return full_text