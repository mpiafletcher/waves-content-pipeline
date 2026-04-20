import os
import requests

WORKER_URL = os.getenv("WORKER_URL")
WORKER_API_KEY = os.getenv("WORKER_API_KEY")

def send_to_putter(script, episode):
    res = requests.post(
        WORKER_URL,
        headers={
            "x-api-key": WORKER_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": script,
            "episode": episode
        }
    )

    return res.json()
