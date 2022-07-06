from dataclasses import field
from rest_framework import serializers
from autoecole_api.models import School,Student,Card,Activity,Session,Employee


class School_serializer(serializers.ModelSerializer):
    class Meta:
        model=School
        fields = '__all__'

class Student_serializer(serializers.ModelSerializer):
    class Meta:
        model=Student
        fields = '__all__'

class Card_serializer(serializers.ModelSerializer):
    class Meta:
        model=Card
        fields = '__all__'

class Activity_serializer(serializers.ModelSerializer):
    class Meta:
        model= Activity
        fields = '__all__'

class Session_serializer(serializers.ModelSerializer):
    class Meta:
        model= Session
        # fields = '__all__'
        fields = (    'day',    'start_at',    'end_at',    'activity',    'price','duration')

class Employee_serializer(serializers.ModelSerializer):
    class Meta:
        model=Student
        fields = '__all__'
