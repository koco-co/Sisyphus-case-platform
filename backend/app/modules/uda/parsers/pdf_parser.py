import io

from pypdf import PdfReader


def parse_pdf(raw_bytes: bytes) -> tuple[str, dict]:
    reader = PdfReader(io.BytesIO(raw_bytes))
    pages_text: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text.strip())

    full_text = "\n\n".join(pages_text)

    # Simple section extraction from text
    sections: list[dict[str, str]] = []
    current_heading = ""
    current_body_lines: list[str] = []

    for line in full_text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        # Heuristic: short lines in all-caps or starting with number could be headings
        if len(line_stripped) < 80 and (line_stripped[0].isdigit() or line_stripped.isupper()):
            if current_heading or current_body_lines:
                sections.append(
                    {
                        "heading": current_heading,
                        "body": "\n".join(current_body_lines).strip(),
                    }
                )
            current_heading = line_stripped
            current_body_lines = []
        else:
            current_body_lines.append(line_stripped)

    if current_heading or current_body_lines:
        sections.append(
            {
                "heading": current_heading,
                "body": "\n".join(current_body_lines).strip(),
            }
        )

    content_ast: dict = {
        "raw_text": full_text,
        "sections": sections,
        "page_count": len(reader.pages),
    }

    return full_text, content_ast
