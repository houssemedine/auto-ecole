from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from uuid import uuid4
from django.conf import settings
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext_lazy as _

# Create your models here.
def avatar_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    unique_name = uuid4().hex  # ex : '3fa85f64f7d24a15a96b0dbab207ac4e'
    return f"avatars/{unique_name}.{ext}"

# BasedModel
class BaseModel(models.Model):
    # created_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.IntegerField( null=True, blank=True)
    updated_by = models.IntegerField( null=True, blank=True)

    class Meta:
        abstract = True


# SoftDeleteManager
# creating a custom model manager to apply the filter
# automatically without using filter(is_delete=False)
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # return super().get_queryset().filter(is_deleted=False)
        return super().get_queryset().all()
# SoftDeleteModel


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(null=False, default=False)
    deleted_by = models.IntegerField( null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    restored_at = models.DateTimeField(null=True, blank=True)
    restored_by = models.IntegerField( null=True, blank=True)

    # objects = models.Manager()
    undeleted_objects = SoftDeleteManager()

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    class Meta:
        # Django will not create a database table for this model
        abstract = True

class User(AbstractUser, SoftDeleteModel):
    USER_TYPE_CHOICES = (
        (1, _("Guest")),
        (2, _("Admin")),
        (3, _("Owner")),
        (4, _("Trainer")),
        (5, _("Student")),
    )

    GENDER = (
        (1, _("Male")),
        (2, _("Female")),
    )

    role = models.PositiveSmallIntegerField(
        _("role"),
        choices=USER_TYPE_CHOICES,
        default=1,
    )
    avatar = models.ImageField(
        _("profile photo"),
        upload_to=avatar_upload_to,
        null=True,
        blank=True,
    )
    school = models.ForeignKey(
        "School",
        on_delete=models.SET_NULL,  # keep original behavior
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("school"),
    )
    phone = models.IntegerField(_("phone"), unique=False, null=True, blank=True)
    full_name = models.CharField(_("full name"), max_length=100, blank=True, null=True)
    birthday = models.DateField(_("birth date"), null=True, blank=True)
    cin = models.CharField(
        _("CIN"),
        max_length=50,
        unique=False,
        db_index=True,
        null=True,
        blank=True,
        error_messages={"unique": _("A user with this CIN already exists.")},
    )
    gender = models.PositiveSmallIntegerField(
        _("gender"),
        null=True,
        blank=True,
        choices=GENDER,
    )
    governorate = models.ForeignKey(
        "Governorate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("governorate"),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "phone"],
                name="uniq_user_school_phone",
            ),
            models.UniqueConstraint(
                fields=["school", "cin"],
                name="uniq_user_school_cin",
            ),
        ]
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        # Friendly message for (school, phone) uniqueness
        if self.school_id and self.phone is not None:
            qs = type(self).objects.filter(school_id=self.school_id, phone=self.phone)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"phone": _("This phone number is already used in this school.")}
                )
            
        if self.school_id and self.cin:
            qs = type(self).objects.filter(school_id=self.school_id, cin=self.cin)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"cin": _("This CIN is already used in this school.")}
                )

    def __str__(self):
        role = "Admin"
        for loop in self.USER_TYPE_CHOICES:
            if loop[0] == self.role:
                role = loop[1]
                break
        return "ID: {} -School: {} - Phone: {} - Role: {}".format(self.id, self.school, self.phone, role)



class OTPPurpose(models.TextChoices):
    REGISTRATION = "registration", "Registration"

class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    purpose = models.CharField(max_length=32, choices=OTPPurpose.choices)
    code_hash = models.CharField(max_length=128)  # hash via make_password
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    is_used = models.BooleanField(default=False)

    channel = models.CharField(max_length=16, choices=[("email", "Email"), ("sms", "SMS")])
    destination = models.CharField(max_length=255)  # email ou n° de téléphone

    class Meta:
        indexes = [
            models.Index(fields=["user", "purpose", "is_used", "expires_at"]),
        ]

    def __str__(self):
        return f"OTP {self.purpose} for {self.user} (used={self.is_used})"



class School(BaseModel, SoftDeleteModel):
    name = models.CharField(_("name"), max_length=100)
    code = models.CharField(
        _("code"),
        max_length=50,
        unique=True,
        error_messages={"unique": _("A school with this code already exists.")},
    )
    adress = models.TextField(_("address"), max_length=150, blank=True, null=True)
    city = models.CharField(_("city"), max_length=50, blank=True, null=True)
    governorate = models.CharField(_("governorate"), max_length=50, blank=True, null=True)
    country = models.CharField(_("country"), max_length=50, blank=True, null=True)
    speciality = models.CharField(_("specialty"), max_length=50, blank=True, null=True)
    email = models.EmailField(_("email"), blank=True, null=True)
    tel = models.IntegerField(_("phone"), blank=True, null=True)
    logo = models.ImageField(_("logo"), blank=True, null=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("school")
        verbose_name_plural = _("schools")

    def __str__(self):
        return f'{self.name} - {self.code}- {self.is_active}'

class UserPreference(BaseModel, SoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(
        'School',
        on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=10, default='en')
    notifications_enabled = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return f'User: {self.user} - School: {self.school}'

class Country(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=50)
    tel_code = models.CharField(max_length=10)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Governorate(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class City(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=50)
    governorate = models.ForeignKey(Governorate, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SchoolSubscription(BaseModel, SoftDeleteModel):
    school = models.ForeignKey(School, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    duration = models.IntegerField()  # in months
    method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other')
    ], default='cash')
    comment = models.TextField(blank=True, null=True)
    trial = models.BooleanField(default=False)
    class Meta:
        ordering = ['school', '-date']

    @property
    def valid_until(self):
        # relativedelta gère correctement les fins de mois (ex: 31/01 + 1 mois -> 28/02)
        return self.date + relativedelta(months=self.duration)

    def __str__(self):
        return f'school: {self.school} - date: {self.date} - duration: {self.duration} mois'

class LicenceType(BaseModel, SoftDeleteModel):
    name=models.CharField(max_length=50)
    comment= models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'Permis: {self.name}'

class Status(BaseModel, SoftDeleteModel):
    name=models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name}'

class Card(BaseModel, SoftDeleteModel):
    school = models.ForeignKey(
        School,
        related_name='school_card',
        on_delete=models.CASCADE,
        verbose_name=_("school"),
    )
    licence_type = models.ForeignKey(
        LicenceType,
        related_name='licence_type',
        on_delete=models.DO_NOTHING,
        verbose_name=_("licence type"),
    )
    start_at = models.DateField(_("start date"))
    end_at = models.DateField(_("end date"), null=True, blank=True)
    student = models.ForeignKey(
        User,
        related_name='student',
        on_delete=models.CASCADE,
        verbose_name=_("student"),
    )
    status = models.ForeignKey(
        Status,
        related_name='status',
        default=1,
        on_delete=models.DO_NOTHING,
        verbose_name=_("status"),
    )
    price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    hour_price = models.DecimalField(
        _("hour price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    hours_number = models.IntegerField(_("number of hours"), null=True, blank=True)
    discount = models.DecimalField(
        _("discount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['licence_type']
        verbose_name = _("card")
        verbose_name_plural = _("cards")

    def __str__(self):
        return f'ID: {self.id} _ Type: {self.licence_type}'


class CardStatusHistory(BaseModel, SoftDeleteModel):
    card = models.ForeignKey(Card,related_name='card_history' ,on_delete=models.CASCADE)
    status =models.ForeignKey(Status, related_name='status_history', on_delete=models.CASCADE)
    date=models.DateField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Card: {self.card}, Status: {self.status}'

class Payment(BaseModel, SoftDeleteModel):
    amount = models.DecimalField(_("amount"), max_digits=10, decimal_places=2)
    date = models.DateField(_("date"))
    motive = models.CharField(_("reason"), max_length=50, null=True, blank=True)
    method = models.CharField(_("method"), max_length=50, default='espéces')  # default conservé tel quel
    card = models.ForeignKey(
        Card,
        related_name='cardP',
        on_delete=models.CASCADE,
        verbose_name=_("card"),
    )

    class Meta:
        ordering = ['-date']
        verbose_name = _("payment")
        verbose_name_plural = _("payments")

    def __str__(self):
        return f'Date: {self.date}'

class Activity(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=50, unique=True)
    duration = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class NotificationType(BaseModel, SoftDeleteManager):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    importance = models.CharField(max_length=50, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.importance})'

class Notification(BaseModel, SoftDeleteModel):
    MODULE_CHOICES = [
        ('car', 'Car'),
        ('session', 'Session'),
        ('payment', 'Payment'),
        ('appointment', 'Appointment'),
        ('student', 'Student'),
        ('card', 'Card'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.ForeignKey('NotificationType', on_delete=models.CASCADE)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, db_index=True)
    title = models.CharField(max_length=100)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # <- payload pour deep link, ids, etc.
    priority = models.CharField(max_length=10, choices=[('normal','Normal'),('high','High')], default='normal')
    category = models.CharField(max_length=50, blank=True)  # <- utile côté iOS (facultatif)
    date_sent = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-date_sent', 'user']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['module', 'date_sent']),
        ]

    def __str__(self):
        return f'{self.title} → {self.user}'

class Device(models.Model):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    PLATFORM_CHOICES = [(ANDROID, "Android"), (IOS, "iOS"), (WEB, "Web")]

    # 🔹 NEW : on distingue le fournisseur de push (Expo ou FCM)
    PROVIDER_CHOICES = [("expo", "Expo"), ("fcm", "FCM")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="devices")
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES, default="expo", db_index=True)  # 👈 NEW (par défaut Expo)
    token = models.CharField(max_length=255, db_index=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, db_index=True)
    app_version = models.CharField(max_length=50, blank=True)
    locale = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.platform} - {self.provider}"

class NotificationDelivery(models.Model):
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'
    STATUS_CHOICES = [(PENDING, 'Pending'), (SENT, 'Sent'), (FAILED, 'Failed')]

    notification = models.ForeignKey('Notification', on_delete=models.CASCADE, related_name='deliveries')
    device = models.ForeignKey('Device', on_delete=models.CASCADE, related_name='deliveries')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    fcm_message_id = models.CharField(max_length=200, blank=True)  # renvoyé par FCM
    error_code = models.CharField(max_length=100, blank=True)
    error_detail = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('notification', 'device')]  # 1 trace par device
        indexes = [
            models.Index(fields=['status', 'updated_at']),
        ]

    def __str__(self):
        return f'{self.notification_id} → {self.device_id} [{self.status}]'

class UserNotificationPreference(BaseModel, SoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)

    class Meta:
        ordering= ['user']

    def __str__(self):
        return f'{self.user}'


class Car(BaseModel, SoftDeleteModel):
    fuel = [
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
        ('Gaz', 'Gaz'),          # laissé tel quel pour ne rien casser
        ('Electric', 'Electric'),
    ]

    serial_number = models.CharField(_("serial number"), max_length=50, unique=True,
                                     error_messages={"unique": _("A car with this serial number already exists.")},
    )
    marque = models.CharField(_("brand"), max_length=50, null=True, blank=True)  # label en anglais
    model = models.CharField(_("model"), max_length=50, null=True, blank=True)
    purchase_date = models.DateField(_("purchase date"), null=True, blank=True)
    fuel_type = models.CharField(_("fuel type"), max_length=50, choices=fuel, blank=True)
    school = models.ForeignKey(School, verbose_name=_("school"), on_delete=models.CASCADE)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        ordering = ['marque']
        verbose_name = _("car")
        verbose_name_plural = _("cars")


    def __str__(self):
        return f'{self.serial_number} | {self.marque} | {self.model}'

class SessionType(BaseModel, SoftDeleteModel):
    name=models.CharField(max_length=50,default='Conduite')
    comment=models.CharField(max_length=100,null=True, blank=True)


    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name}'


class Session(BaseModel, SoftDeleteModel):
    day = models.DateField(_("day"))
    start_at = models.TimeField(_("start time"))
    end_at = models.TimeField(_("end time"))
    card = models.ForeignKey(
        Card,
        related_name="card",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("card"),
    )
    employee = models.ForeignKey(
        User,
        related_name="employee",
        on_delete=models.CASCADE,
        verbose_name=_("employee"),
    )
    school = models.ForeignKey(
        School,
        related_name="school",
        on_delete=models.CASCADE,
        verbose_name=_("school"),
    )
    car = models.ForeignKey(
        Car,
        related_name="car",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        verbose_name=_("car"),
    )
    note = models.CharField(_("note"), max_length=100, null=True, blank=True)
    session_type = models.ForeignKey(
        SessionType,
        related_name="session_type",
        on_delete=models.DO_NOTHING,
        default="4",
        verbose_name=_("session type"),
    )
    event_type = models.CharField(
        _("event type"),
        max_length=50,
        choices=[("session", _("Session")), ("other", _("other"))],
        default="session",
    )
    is_cancelled = models.BooleanField(_("cancelled"), default=False)
    price = models.DecimalField(
        _("price"), max_digits=5, decimal_places=2, null=True, blank=True
    )

    def clean(self):
        super().clean()
        if self.event_type == "session":
            if not self.card:
                raise ValidationError(
                    {"card": _("Card is required for event type 'session'.")}
                )
            if not self.session_type:
                raise ValidationError(
                    {"session_type": _("Session type is required for event type 'session'.")}
                )

    class Meta:
        ordering = ["day"]
        verbose_name = _("session")
        verbose_name_plural = _("sessions")

    def __str__(self):
        return self.day.strftime("%d %b, %Y")

    # Session duration calcul
    @property
    def duration(self):
        date = datetime.date(1, 1, 1)
        datetime1 = datetime.datetime.combine(date, self.end_at)
        datetime2 = datetime.datetime.combine(date, self.start_at)
        return (datetime1 - datetime2)/3600
