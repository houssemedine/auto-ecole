from dataclasses import field
from rest_framework import serializers
from autoecole_api.models import *


class User_serializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = '__all__'
class Country_serializer(serializers.ModelSerializer):

    class Meta:
        model= Country
        fields = '__all__'

class Governorate_serializer(serializers.ModelSerializer):
    country = Country_serializer()

    class Meta:
        model= Governorate
        fields = '__all__'

class City_serializer(serializers.ModelSerializer):
    governorate = Governorate_serializer()

    class Meta:
        model= City
        fields = '__all__'

class School_serializer(serializers.ModelSerializer):
    class Meta:
        model=School
        fields = '__all__'

class Student_serializer_read(serializers.ModelSerializer):
    city = City_serializer()

    class Meta:
        model=Student
        fields = '__all__'

class Student_serializer(serializers.ModelSerializer):
    # avatar = serializers.SerializerMethodField()

    class Meta:
        model=Student
        fields = '__all__'

    # def get_avatar(self, obj):
    #     request = self.context.get("request")
    #     if obj.avatar and hasattr(obj.avatar, 'url'):
    #         return request.build_absolute_uri(obj.avatar.url)
    #     return None





class Card_serializer(serializers.ModelSerializer):
    class Meta:
        model=Card
        fields = '__all__'
        # fields =('student', 'licence_type')

class Card_status_serializer(serializers.ModelSerializer):
    class Meta:
        model=CardStatusHistory
        fields = '__all__'
        # fields =('student', 'licence_type')



class Activity_serializer(serializers.ModelSerializer):
    class Meta:
        model= Activity
        fields = '__all__'

class Licence_serializer(serializers.ModelSerializer):
    class Meta:
        model= LicenceType
        fields = '__all__'


class Status_serializer(serializers.ModelSerializer):
    class Meta:
        model= Status
        fields = '__all__'

class Card_status_serializer_read(serializers.ModelSerializer):
    status = Status_serializer()

    class Meta:
        model = CardStatusHistory
        fields = '__all__'

class Payments_serializer(serializers.ModelSerializer):
    class Meta:
        model= Payment
        fields = '__all__'

class Card_serializer_read(serializers.ModelSerializer):
    student = Student_serializer()
    licence_type = Licence_serializer()
    status = Status_serializer()
    # payments = Payments_serializer(many=True, read_only=True)

    class Meta:
        model=Card
        fields = '__all__'

class Session_serializer_edit(serializers.ModelSerializer):
    class Meta:
        model= Session
        fields = '__all__'
        # fields = ('day','start_at','end_at','activity','price','duration')

class Employee_serializer_read(serializers.ModelSerializer):
    city=City_serializer()
    class Meta:
        model=Employee
        fields = '__all__'

class Employee_serializer(serializers.ModelSerializer):
    class Meta:
        model=Employee
        fields = '__all__'

class Owner_serializer(serializers.ModelSerializer):
    class Meta:
        model=Owner
        fields = '__all__'


class Car_serializer(serializers.ModelSerializer):
    class Meta:
        model=Car
        fields = '__all__'


class SessionTypes_serializer(serializers.ModelSerializer):
    class Meta:
        model=SessionType
        fields = '__all__'


class Session_serializer_read(serializers.ModelSerializer):
    card=Card_serializer_read()
    session_type = SessionTypes_serializer()
    employee = Employee_serializer()
    car = Car_serializer()

    class Meta:
        model= Session
        fields = '__all__'
        # fields = ('day','start_at','end_at','activity','price','duration')

class NotificationType_serializer(serializers.ModelSerializer):
    class Meta:
        model= NotificationType
        fields = '__all__'


class Notification_serializer(serializers.ModelSerializer):
    class Meta:
        model= Notification
        fields = '__all__'


class Notification_serializer_read(serializers.ModelSerializer):
    user = User_serializer()
    notification_type=NotificationType_serializer()

    class Meta:
        model= Notification
        fields = '__all__'



