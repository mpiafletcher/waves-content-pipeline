import hashlib
from datetime import datetime

def build_dedupe_key(title, url):
    base = f"{title.strip().lower()}_{url.strip()}"
    return hashlib.sha256(base.encode()).hexdigest()[:32]

def build_variant_key(dedupe_key, language):
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"{dedupe_key}_{today}_{language}"
