# notifications/senders/expo.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import requests

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

@dataclass
class SendResult:
    success: bool
    message_id: Optional[str] = None
    error_code: Optional[str] = None     # "DeviceNotRegistered", "SEND_ERROR", etc.
    error_detail: Optional[str] = None
    deactivate_device: bool = False

def send_push_expo(*, token: str, title: str, body: str,
                    data: Optional[Dict[str, Any]] = None) -> SendResult:
    try:
        resp = requests.post(EXPO_PUSH_URL, json={
            "to": token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": "default",
        }, timeout=10)
        resp.raise_for_status()
        j = resp.json() or {}
        d = j.get("data") or {}
        if d.get("status") == "ok":
            return SendResult(success=True, message_id=d.get("id", ""))
        err = (d.get("details") or {}).get("error") or d.get("message") or "SEND_ERROR"
        deactivate = err in ("DeviceNotRegistered", "DeviceNotRegisteredError")
        return SendResult(success=False, error_code=err, error_detail=str(j), deactivate_device=deactivate)
    except Exception as e:
        return SendResult(success=False, error_code="SEND_ERROR", error_detail=str(e))
