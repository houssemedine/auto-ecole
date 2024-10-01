from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Create your models here.
class User(AbstractUser):
    USER_TYPE_CHOICES = (
    (1, 'Guest'),
    (2, 'Admin'),
    (3, 'Owner'),
    (4, 'Trainer'),
    (5, 'Student'),
    )

    fonction = models.PositiveSmallIntegerField(
        choices=USER_TYPE_CHOICES,
        default=1
        )
    avatar = models.ImageField(
        verbose_name='photo de profile',
        upload_to='media/avatars',
        null=True,
        blank=True
        )

    def __str__(self):
        fonction = "Admin"
        for loop in self.USER_TYPE_CHOICES:
            if loop[0] == self.fonction:
                fonction = loop[1]
                break
        return "{} : {}".format(self.username, fonction)

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
        return super().get_queryset().filter(is_deleted=False)
        # return super().get_queryset().all()
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

# Owner Model


class Owner(BaseModel, SoftDeleteModel, User):
    roles = [
        ('Manager', 'Manager'),
        ('Trainer', 'Trainer'),
    ]

    role = models.CharField(max_length=100, choices=roles, default='Manager')
    # city = models.CharField(max_length=50)
    # governorate = models.CharField(max_length=50)
    # country = models.CharField(max_length=50)
    tel = models.IntegerField(unique=True)
    birthday = models.DateField(blank=True, null=True)


# School model
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
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)

    # users=models.ManyToManyField(User)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Student(BaseModel, SoftDeleteModel, User):
    # name=models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    governorate = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    tel = models.IntegerField(blank=True, null=True, unique=True)
    birthday = models.DateField()
    gender=models.CharField(max_length=50,default='male')
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    # user=models.ForeignKey(User,on_delete=models.CASCADE)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username

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

# class Progress(BaseModel, SoftDeleteModel):
#     name=models.CharField(max_length=50, unique=True)

#     class Meta:
#         ordering = ['id']

#     def __str__(self):
#         return f'{self.name}'

class Card(BaseModel, SoftDeleteModel):
    status = [
        ('1', 'In progress'),
        ('2', 'Completed'),
        ('3', 'Canceled'),
    ]
    licence_type = models.ForeignKey(LicenceType,related_name='licence_type' ,on_delete=models.CASCADE)
    start_at = models.DateField()
    end_at = models.DateField(null=True, blank=True)
    student = models.ForeignKey(Student,related_name='student' ,on_delete=models.CASCADE)
    status = models.ForeignKey(Status,related_name='status',default=1, on_delete=models.CASCADE)
    # if True price will be an input, if false price will be calucle in proprety
    manual_price = models.BooleanField(null=True, blank=True)
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


class NotificationType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    importance = models.CharField(max_length=50, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}'

class Notification(BaseModel, SoftDeleteManager):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return f'{self.user}'

class UserNotificationPreference(BaseModel, SoftDeleteManager):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)

    class Meta:
        ordering= ['user']

    def __str__(self):
        return f'{self.user}'

class Employee(BaseModel, SoftDeleteModel, User):
    roles = [
        ('Manager', 'Manager'),
        ('Trainer', 'Trainer'),
    ]
    matricule=models.CharField(max_length=50,unique=True)
    role = models.CharField(max_length=100, choices=roles, default='Trainer')
    city = models.CharField(max_length=50)
    governorate = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    tel = models.IntegerField()
    birthday = models.DateField()
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    image=models.ImageField(blank=True,null=True)


    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username


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

    class Meta:
        ordering = ['marque']

    def __str__(self):
        return f'{self.serial_number} | {self.marque} | {self.model}'

class SessionType(BaseModel, SoftDeleteModel):
    name=models.CharField(max_length=50,default='Conduite')
    comment=models.CharField(max_length=100,null=True, blank=True)


    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}'


class Session(BaseModel, SoftDeleteModel):
    day = models.DateField()
    start_at = models.TimeField()
    end_at = models.TimeField()
    card = models.ForeignKey(Card,related_name='card' ,on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee,related_name='employee' ,on_delete=models.CASCADE)
    car = models.ForeignKey(Car,related_name='car' ,on_delete=models.CASCADE,null=True, blank=True)
    note=models.CharField(max_length=100,null=True, blank=True)
    session_type = models.ForeignKey(SessionType,related_name='session_type' ,on_delete=models.CASCADE)

    price = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)

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
