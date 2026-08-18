import os
import requests

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")


def send_to_make(payload):
    if not MAKE_WEBHOOK_URL:
        return {
            "success": False,
            "error": "MAKE_WEBHOOK_URL is missing"
        }

    try:
        res = requests.post(
            MAKE_WEBHOOK_URL,
            json=payload,
            timeout=90
        )

        if res.ok:
            try:
                data = res.json()
            except Exception:
                data = res.text

            return {
                "success": True,
                "status": res.status_code,
                "data": data
            }

        return {
            "success": False,
            "status": res.status_code,
            "error": res.text
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
