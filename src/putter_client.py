import os
import requests

WORKER_URL = os.getenv("WORKER_URL")
WORKER_API_KEY = os.getenv("WORKER_API_KEY")

def send_to_putter(script, episode):
    if not isinstance(script, str) or not script.strip():
        raise ValueError("script must be a non-empty string")

    res = requests.post(
        WORKER_URL,
        headers={
            "x-api-key": WORKER_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": script,
            "episode": episode
        },
        timeout=60
    )

    res.raise_for_status()
    return res.json()
