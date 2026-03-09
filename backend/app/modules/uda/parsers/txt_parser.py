def parse_txt(raw_bytes: bytes) -> tuple[str, dict]:
    text = raw_bytes.decode("utf-8", errors="replace")
    content_ast: dict = {
        "raw_text": text,
        "sections": [{"heading": "", "body": text}],
    }
    return text, content_ast
