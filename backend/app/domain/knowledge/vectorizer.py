def build_embedding_payload(asset: dict) -> str:
    title = asset.get('title', '')
    summary = asset.get('summary', '')
    return f'{title}\n{summary}'.strip()
