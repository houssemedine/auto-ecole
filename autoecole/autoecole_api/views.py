from datetime import datetime
from tkinter import TRUE
from django.shortcuts import render
from autoecole_api.models import School
from autoecole_api.serializers import School_serializer
from rest_framework.decorators import  api_view
from rest_framework.response import Response
from rest_framework import status
# Create your views here.


#School CRUD
@api_view(['GET','POST'])
def school(request):
    if request.method=='GET':
        if not (schools := School.objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=School_serializer(schools,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=School_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
def school_edit(request,id):
    try:
        school=School.objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method=='GET':
        serializer=School_serializer(school)
        return Response (serializer.data,status=status.HTTP_200_OK)
    if request.method=='PUT':
        serializer=School_serializer(school,data=request.data)
        if not (serializer.is_valid()):
            return Response (serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response (serializer.data,status=status.HTTP_201_CREATED)
    if request.method=='DELETE':
        school.is_deleted=True
        school.deleted_at=datetime.now()
        school.save()
        serializer=School_serializer(school)
        return Response(status=status.HTTP_201_CREATED)