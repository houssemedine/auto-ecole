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

class SchoolSubscription_serializer(serializers.ModelSerializer):
    class Meta:
        model=SchoolSubscription
        fields = '__all__'

class Student_serializer_read(serializers.ModelSerializer):
    governorate = Governorate_serializer()

    class Meta:
        model=User
        fields = '__all__'

class Student_serializer(serializers.ModelSerializer):
    # avatar = serializers.SerializerMethodField()

    class Meta:
        model=User
        fields = '__all__'

    # def get_avatar(self, obj):
    #     request = self.context.get("request")
    #     if obj.avatar and hasattr(obj.avatar, 'url'):
    #         return request.build_absolute_uri(obj.avatar.url)
    #     return None

class User_Preference_serializer(serializers.ModelSerializer):
    class Meta:
        model=UserPreference
        fields = '__all__'

class User_Preference_serializer_read(serializers.ModelSerializer):
    user = User_serializer()
    school = School_serializer()
    class Meta:
        model=UserPreference
        fields = '__all__'

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

class User_serializer_read(serializers.ModelSerializer):
    governorate = Governorate_serializer()
    class Meta:
        model=User
        exclude = ('password', )


class User_serializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = '__all__'

class User_serializer_register(serializers.ModelSerializer):
    class Meta:
        model=User
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
    employee = User_serializer()
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

class NotificationCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    notification_type_id = serializers.IntegerField()
    module = serializers.CharField()
    title = serializers.CharField(max_length=100)
    message = serializers.CharField()
    data = serializers.JSONField(required=False)
    priority = serializers.ChoiceField(choices=[('normal','Normal'), ('high','High')], default='normal')
    category = serializers.CharField(required=False, allow_blank=True)

class DeviceRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=Device.PLATFORM_CHOICES)
    provider = serializers.ChoiceField(choices=Device.PROVIDER_CHOICES, default="expo")  # ← NEW
    app_version = serializers.CharField(max_length=50, required=False, allow_blank=True)
    locale = serializers.CharField(max_length=10, required=False, allow_blank=True)

class DeviceUnregisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)

class DevicePingSerializer(serializers.Serializer):
    app_version = serializers.CharField(max_length=50, required=False, allow_blank=True)
    locale = serializers.CharField(max_length=10, required=False, allow_blank=True)

class NotificationSendSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField()

class Notification_serializer_read(serializers.ModelSerializer):
    user = User_serializer()
    notification_type=NotificationType_serializer()

    class Meta:
        model= Notification
        fields = '__all__'



