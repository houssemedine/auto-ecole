# notifications/senders/fcm.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import os
import firebase_admin
from firebase_admin import credentials, initialize_app, messaging

# ⚠️ adapte le chemin si besoin (tu peux lire depuis settings)
FIREBASE_CRED_PATH = "/Users/houssem/Documents/Projects/kreno-7348a-firebase-service-account.json"

@dataclass
class SendResult:
    success: bool
    message_id: Optional[str] = None
    error_code: Optional[str] = None     # "UNREGISTERED" | "INVALID_TOKEN" | "SEND_ERROR"
    error_detail: Optional[str] = None
    deactivate_device: bool = False

def _init_firebase_if_needed():
    if not firebase_admin._apps and os.path.exists(FIREBASE_CRED_PATH):
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        initialize_app(cred)

def send_push_fcm(*, token: str, title: str, body: str,
                  data: Optional[Dict[str, Any]] = None,
                  priority: str = "normal",
                  category: str = "") -> SendResult:
    """Envoi FCM pur (pas de DB)."""
    _init_firebase_if_needed()
    try:
        msg = messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            android=messaging.AndroidConfig(priority="high" if priority == "high" else "normal"),
            apns=messaging.APNSConfig(headers={"apns-priority": "10" if priority == "high" else "5"}),
        )
        mid = messaging.send(msg)
        return SendResult(success=True, message_id=mid)
    except Exception as e:
        lowers = str(e).lower()
        if "unregistered" in lowers or "registration-token-not-registered" in lowers:
            return SendResult(success=False, error_code="UNREGISTERED", error_detail=str(e), deactivate_device=True)
        if "invalid" in lowers and "token" in lowers:
            return SendResult(success=False, error_code="INVALID_TOKEN", error_detail=str(e), deactivate_device=True)
        return SendResult(success=False, error_code="SEND_ERROR", error_detail=str(e))
