def parse_markdown(raw_bytes: bytes) -> tuple[str, dict]:
    text = raw_bytes.decode("utf-8", errors="replace")

    sections: list[dict[str, str]] = []
    current_heading = ""
    current_body_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("#"):
            if current_heading or current_body_lines:
                sections.append(
                    {
                        "heading": current_heading,
                        "body": "\n".join(current_body_lines).strip(),
                    }
                )
            current_heading = line.lstrip("#").strip()
            current_body_lines = []
        else:
            current_body_lines.append(line)

    if current_heading or current_body_lines:
        sections.append(
            {
                "heading": current_heading,
                "body": "\n".join(current_body_lines).strip(),
            }
        )

    content_ast: dict = {
        "raw_text": text,
        "sections": sections,
    }

    return text, content_ast
