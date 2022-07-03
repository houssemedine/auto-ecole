from dataclasses import field
from rest_framework import serializers
from autoecole_api.models import School,Student,Card


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

