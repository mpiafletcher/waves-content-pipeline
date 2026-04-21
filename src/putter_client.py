import os
import requests

WORKER_URL = os.getenv("WORKER_URL")
WORKER_API_KEY = os.getenv("WORKER_API_KEY")


def send_to_putter(payload):
    try:
        res = requests.post(
            WORKER_URL,
            headers={
                "x-api-key": WORKER_API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=90
        )

        if res.ok:
            return {
                "success": True,
                "status": res.status_code,
                "data": res.json()
            }

        print("PUTTER STATUS:", res.status_code)
        print("PUTTER BODY:", res.text)
        print("PUTTER PAYLOAD PREVIEW:", {
            "text_preview": payload.get("text", "")[:200],
            "path": payload.get("path"),
            "category": payload.get("category"),
            "options": payload.get("options"),
            "episode": payload.get("episode")
        })

        return {
            "success": False,
            "status": res.status_code,
            "error": res.text
        }

    except Exception as e:
        print("PUTTER EXCEPTION:", str(e))
        return {
            "success": False,
            "error": str(e)
        }
