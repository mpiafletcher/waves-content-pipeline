import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def fetch_sources():
    url = f"{SUPABASE_URL}/rest/v1/category_sources"
    
    params = {
        "select": "id,source_name,source_url,priority,category_id,language,source_language,region,categories(name)",
        "is_active": "eq.true",
        "order": "category_id.asc,priority.asc"
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    
    return res.json()
