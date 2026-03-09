import logging

logger = logging.getLogger(__name__)


def parse_document(filename: str, raw_bytes: bytes) -> tuple[str, dict]:
    """Parse document based on file extension. Returns (full_text, content_ast)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "docx":
        from app.modules.uda.parsers.docx_parser import parse_docx

        return parse_docx(raw_bytes)
    elif ext == "pdf":
        from app.modules.uda.parsers.pdf_parser import parse_pdf

        return parse_pdf(raw_bytes)
    elif ext == "md":
        from app.modules.uda.parsers.md_parser import parse_markdown

        return parse_markdown(raw_bytes)
    elif ext in ("txt", "text"):
        from app.modules.uda.parsers.txt_parser import parse_txt

        return parse_txt(raw_bytes)
    elif ext in ("png", "jpg", "jpeg", "gif", "bmp", "webp"):
        # For images, we just note the file type — OCR not implemented yet
        return f"[Image file: {filename}]", {"raw_text": f"[Image file: {filename}]", "sections": []}
    else:
        # Try to read as text
        try:
            text = raw_bytes.decode("utf-8", errors="replace")
            return text, {"raw_text": text, "sections": [{"heading": "", "body": text}]}
        except Exception:
            return f"[Unsupported file: {filename}]", {"raw_text": "", "sections": []}
