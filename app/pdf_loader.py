from pypdf import PdfReader
import io


def extract_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return text


def safe_extract(file_bytes: bytes) -> tuple[str, str | None]:
    """Returns (text, error). error is None on success."""
    try:
        text = extract_text(file_bytes)
    except Exception:
        return "", "Could not parse PDF. Please upload a text-based PDF."

    if not text:
        return "", "We couldn't read your PDF — try copy-pasting your resume as text."

    return text, None
