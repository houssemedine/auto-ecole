# notifications/services.py
from django.db import transaction
from .models import Notification, Device, NotificationDelivery

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
