from __future__ import annotations
from typing import Dict
from django.utils import timezone
from autoecole_api.models import NotificationDelivery, Device
from ..notifications.senders.expo import send_push_expo
from ..notifications.senders.fcm import send_push_fcm

def send_delivery(delivery_id: int) -> None:
    """Charge 1 NotificationDelivery, route vers Expo/FCM, et met à jour la ligne."""
    try:
        delivery = NotificationDelivery.objects.select_related("notification", "device").get(pk=delivery_id)
    except NotificationDelivery.DoesNotExist:
        return

    if delivery.status != NotificationDelivery.PENDING:
        return

    notif = delivery.notification
    device = delivery.device

    # Route selon provider
    if device.provider == "expo":
        res = send_push_expo(
            token=device.token,
            title=notif.title,
            body=notif.message,
            data=notif.data or {},
        )
    else:
        res = send_push_fcm(
            token=device.token,
            title=notif.title,
            body=notif.message,
            data=notif.data or {},
            priority=getattr(notif, "priority", "normal"),
            category=getattr(notif, "category", "") or "",
        )

    # Mise à jour DB
    if res.success:
        delivery.status = NotificationDelivery.SENT
        delivery.fcm_message_id = res.message_id or ""
        delivery.sent_at = timezone.now()
        delivery.error_code = ""
        delivery.error_detail = ""
        delivery.save(update_fields=["status","fcm_message_id","sent_at","error_code","error_detail","updated_at"])
    else:
        delivery.status = NotificationDelivery.FAILED
        delivery.error_code = res.error_code or "SEND_ERROR"
        delivery.error_detail = res.error_detail or ""
        delivery.save(update_fields=["status","error_code","error_detail","updated_at"])
        if res.deactivate_device:
            Device.objects.filter(pk=device.pk).update(is_active=False)

def send_pending_deliveries_for_notification(notification_id: int) -> Dict[str, int]:
    """Envoie toutes les deliveries PENDING d’une notification."""
    pending_ids = list(
        NotificationDelivery.objects
        .filter(notification_id=notification_id, status=NotificationDelivery.PENDING)
        .values_list("id", flat=True)
    )
    total = len(pending_ids)
    for d_id in pending_ids:
        send_delivery(d_id)

    success = NotificationDelivery.objects.filter(notification_id=notification_id, status=NotificationDelivery.SENT).count()
    failed = NotificationDelivery.objects.filter(notification_id=notification_id, status=NotificationDelivery.FAILED).count()
    return {"total": total, "success": success, "failed": failed}
