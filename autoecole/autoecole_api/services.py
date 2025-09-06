# notifications/services.py
from django.db import transaction
from .models import Notification, Device, NotificationDelivery, OTPCode, OTPPurpose
import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
import os
import requests



@transaction.atomic
def create_notification_with_deliveries(*, user, notification_type, module, title, message,
                                        data=None, priority="normal", category=""):
    
    
    notif = Notification.undeleted_objects.create(
        user=user,
        notification_type=notification_type,
        module=module,
        title=title,
        message=message,
        data=data or {},
        priority=priority,
        category=category,
    )

    devices = Device.objects.filter(user=user, is_active=True)
    deliveries = [
        NotificationDelivery(notification=notif, device=d, status=NotificationDelivery.PENDING)
        for d in devices
    ]
    if deliveries:
        NotificationDelivery.objects.bulk_create(deliveries)

    return notif









# --- Helper pour SMS (optionnel) ---
def send_sms(phone_number: str, message: str):
    url = os.getenv("SMS_API_URL")
    api_key = os.getenv("SMS_KEY")
    sender = os.getenv("SMS_SENDER")
    if not api_key:
        return False

    params = {
        "fct": "sms",
        "key": api_key,
        "mobile": phone_number,
        "sms": message,
    }
    if sender:
        params["sender"] = sender

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        print(resp)
        return True
    except requests.exceptions.RequestException as e:
        print("Échec d'envoi SMS: %s", e)
        return False

def _generate_numeric_code(length: int = 6) -> str:
    # 6 chiffres, zéro-pad si besoin (ex: 000123)
    return f"{secrets.randbelow(10**length):0{length}d}"

def create_and_send_otp(user, purpose=OTPPurpose.REGISTRATION, *,
                        channel="email", message_type="otp", destination=None,
                        ttl_minutes=10) -> OTPCode:
    """
    Crée un OTP (hashé), invalide les OTP précédents non utilisés pour ce purpose,
    l'envoie via le canal choisi, et renvoie l'objet OTPCode.
    """
    now = timezone.now()

    # Invalider les anciens OTP actifs pour éviter plusieurs codes valides en parallèle
    OTPCode.objects.filter(
        user=user, purpose=purpose, is_used=False, expires_at__gt=now
    ).update(is_used=True)

    code = _generate_numeric_code(6)
    print('code otp', code)
    code_hash = make_password(code)
    if destination is None:
        destination = user.email if channel == "email" else getattr(user, "phone_number", "")

    otp = OTPCode.objects.create(
        user=user,
        purpose=purpose,
        code_hash=code_hash,
        created_at=now,
        expires_at=now + timedelta(minutes=ttl_minutes),
        attempts=0,
        max_attempts=5,
        is_used=False,
        channel=channel,
        destination=destination,
    )

    # Envoi
    # msg = "Kreno"
    if message_type == 'otp':
        msg = f"Kreno: votre code de vérification est : {code}\nIl expire dans {ttl_minutes} minutes."
    elif message_type == 'password':
        msg = f"Kreno: votre mot de passe temporaire est: {code}, ne le partagez avec personne."

    if channel == "email":
        send_mail(
            subject="Votre code de vérification",
            message=msg,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[destination],
            fail_silently=False,
        )
    elif channel == "sms":
        send_sms(destination, msg)

    return otp