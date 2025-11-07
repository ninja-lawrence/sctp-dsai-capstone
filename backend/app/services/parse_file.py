from typing import Optional
from io import BytesIO

from docx import Document
from PyPDF2 import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        pages = []
        for p in reader.pages[:50]:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                continue
        return "\n".join(pages)[:10000]
    if name.endswith(".docx"):
        doc = Document(BytesIO(content))
        text = "\n".join([p.text for p in doc.paragraphs])
        return text[:10000]
    # default txt
    try:
        return content.decode("utf-8", errors="ignore")[:10000]
    except Exception:
        return ""


