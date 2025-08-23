from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from uuid import uuid4
from django.conf import settings
from dateutil.relativedelta import relativedelta

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
    (1, 'Guest'),
    (2, 'Admin'),
    (3, 'Owner'),
    (4, 'Trainer'),
    (5, 'Student'),
    )

    GENDER = (
    (1, 'Male'),
    (2, 'Female'),
    )

    role = models.PositiveSmallIntegerField(
        choices=USER_TYPE_CHOICES,
        default=1
        )
    avatar = models.ImageField(
        verbose_name='photo de profile',
        upload_to=avatar_upload_to,
        null=True,
        blank=True
        )

    school = models.ForeignKey(
        'School',
        on_delete=models.SET_NULL,  # évite d'effacer l'utilisateur si l'école est supprimée
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.IntegerField(unique=False, null=True, blank=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    cin = models.CharField(max_length=50, unique=True, null=True, blank=True)
    gender = models.PositiveSmallIntegerField(null=True, blank=True, choices=GENDER)
    governorate = models.ForeignKey(
        'Governorate',
        on_delete=models.SET_NULL,  # évite d'effacer l'utilisateur si la ville est supprimée
        null=True,
        blank=True,
        related_name='users',
    )

    class Meta:
        constraints = [
            # 3) Unicité par (école, téléphone) = “clé composée” logique
            models.UniqueConstraint(fields=['school', 'phone'], name='uniq_user_school_phone'),
        ]

    def __str__(self):
        role = "Admin"
        for loop in self.USER_TYPE_CHOICES:
            if loop[0] == self.role:
                role = loop[1]
                break
        return "School: {} - Phone: {} - Role: {}".format(self.school, self.phone, role)

class School(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=100)
    code=models.CharField(max_length=50,unique=True)
    adress = models.TextField(max_length=150,blank=True, null=True)
    city = models.CharField(max_length=50,blank=True, null=True)
    governorate = models.CharField(max_length=50,blank=True, null=True)
    country = models.CharField(max_length=50,blank=True, null=True)
    speciality = models.CharField(max_length=50,blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    tel = models.IntegerField(blank=True, null=True)
    logo = models.ImageField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

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


class SchoolPayment(BaseModel, SoftDeleteModel):
    school = models.ForeignKey(School, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=99999999, decimal_places=2)
    date = models.DateField()
    duration = models.IntegerField()  # in months
    method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other')
    ], default='cash')
    comment = models.TextField(blank=True, null=True)

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
    # status = [
    #     ('1', 'In progress'),
    #     ('2', 'Completed'),
    #     ('3', 'Canceled'),
    # ]
    school = models.ForeignKey(School,related_name='school_card' ,on_delete=models.CASCADE)
    licence_type = models.ForeignKey(LicenceType,related_name='licence_type' ,on_delete=models.DO_NOTHING)
    start_at = models.DateField()
    end_at = models.DateField(null=True, blank=True)
    student = models.ForeignKey(User,related_name='student' ,on_delete=models.CASCADE)
    status = models.ForeignKey(Status,related_name='status',default=1, on_delete=models.DO_NOTHING)
    # if True price will be an input, if false price will be calucle in proprety
    # manual_price = models.BooleanField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=99999999, decimal_places=2, null=True, blank=True)
    hour_price = models.DecimalField(
        max_digits=99999999, decimal_places=2, null=True, blank=True)
    hours_number = models.IntegerField(null=True, blank=True)
    discount = models.DecimalField(
        max_digits=99999999, decimal_places=2, null=True, blank=True)
    # progress = models.ForeignKey(Progress,related_name='progress' ,on_delete=models.CASCADE, default=1)


    class Meta:
        ordering = ['licence_type']

    def __str__(self):
        return f'ID: {self.id} _ Type: {self.licence_type}'

    # @property
    # def total_price(self):
    #     total_price=((self.hours_number*self.hour_price)*self.discount)/100
    #     return total_price

class CardStatusHistory(BaseModel, SoftDeleteModel):
    card = models.ForeignKey(Card,related_name='card_history' ,on_delete=models.CASCADE)
    status =models.ForeignKey(Status, related_name='status_history', on_delete=models.CASCADE)
    date=models.DateField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Card: {self.card}, Status: {self.status}'

class Payment(BaseModel, SoftDeleteModel):
    amount=models.DecimalField(max_digits=99999999, decimal_places=2)
    date=models.DateField()
    motive=models.CharField(max_length=50)
    method=models.CharField(max_length=50, default='espéces')
    card=models.ForeignKey(Card, related_name='cardP' ,on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date']

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
    token = models.CharField(max_length=255, unique=True)
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
        ('Gaz', 'Gaz'),
        ('Electric', 'Electric'),
    ]
    serial_number = models.CharField(max_length=50, unique=True)
    marque = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    fuel_type = models.CharField(max_length=50, choices=fuel, blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['marque']

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
    day = models.DateField()
    start_at = models.TimeField()
    end_at = models.TimeField()
    card = models.ForeignKey(Card,related_name='card' ,on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(User,related_name='employee' ,on_delete=models.CASCADE)
    car = models.ForeignKey(Car,related_name='car' ,on_delete=models.DO_NOTHING,null=True, blank=True)
    note=models.CharField(max_length=100,null=True, blank=True)
    session_type = models.ForeignKey(SessionType,related_name='session_type' ,on_delete=models.DO_NOTHING, default='4')
    event_type = models.CharField(
        max_length=50, choices=[('session', 'Session'), ('other', 'other')], default='session')
    is_cancelled = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)

    def clean(self):
            super().clean()

            if self.event_type == 'session':
                if not self.card:
                    raise ValidationError({'card': "Card is required for session type 'session'"})
                if not self.session_type:
                    raise ValidationError({'session_type': "Session type is required for event type 'session'"})
    class Meta:
        ordering = ['day']

    def __str__(self):
        return self.day.strftime("%d %b, %Y")

    # Session duration calcul
    @property
    def duration(self):
        date = datetime.date(1, 1, 1)
        datetime1 = datetime.datetime.combine(date, self.end_at)
        datetime2 = datetime.datetime.combine(date, self.start_at)
        return (datetime1 - datetime2)/3600
