def score_asset(query: str, asset: dict) -> float:
    haystack = f"{asset.get('title', '')} {asset.get('summary', '')}".lower()
    return 1.0 if query.lower() in haystack and query else 0.0
