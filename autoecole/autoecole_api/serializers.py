from dataclasses import field
from rest_framework import serializers
from autoecole_api.models import School


class School_serializer(serializers.ModelSerializer):
    class Meta:
        model=School
        fields = '__all__'

