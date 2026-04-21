import os
import requests

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")


def send_to_make(payload):
    try:
        res = requests.post(
            MAKE_WEBHOOK_URL,
            json=payload,
            timeout=90
        )

        return {
            "success": res.ok,
            "status": res.status_code,
            "response": res.text
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
