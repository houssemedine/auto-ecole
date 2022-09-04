from datetime import datetime
from autoecole_api.models import *
from autoecole_api.serializers import *
from rest_framework.decorators import  api_view , permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from autoecole_api.permissions import IsManager

#Custom JWT to obtain more information
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

#School CRUD
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated,IsManager])
def school(request):
    #Get connected user
    user=request.user
    if request.method=='GET':
        if not (schools := user.school_set.all()):
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

#Student CRUD
@api_view(['GET','POST'])
# @permission_classes([IsAuthenticated])
def student(request):
    if request.method=='GET':
        if not (students := Student.objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Student_serializer(students,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=Student_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
# @permission_classes([IsAuthenticated])
def student_edit(request,id):
    try:
        student=Student.objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method=='GET':
        serializer=Student_serializer(student)
        return Response (serializer.data,status=status.HTTP_200_OK)
    if request.method=='PUT':
        serializer=Student_serializer(student,data=request.data)
        if not (serializer.is_valid()):
            return Response (serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response (serializer.data,status=status.HTTP_201_CREATED)
    if request.method=='DELETE':
        student.is_deleted=True
        student.deleted_at=datetime.now()
        student.save()
        serializer=Student_serializer(student)
        return Response(status=status.HTTP_201_CREATED)

#Card CRUD
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def card(request):
    user=request.user
    print(user)
    if request.method=='GET':
        if not (cards := Card.objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Card_serializer(cards,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=Card_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        if serializer.validated_data['manual_price']:
            if not serializer.validated_data['price']:
                return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer.validated_data['price']= (serializer.validated_data['hours_number']*serializer.validated_data['hour_price']) * (1 - (serializer.validated_data['discount']/100))
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
@permission_classes([IsAuthenticated])
def card_edit(request,id):
    try:
        card=Card.objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method=='GET':
        serializer=Card_serializer(card)
        return Response (serializer.data,status=status.HTTP_200_OK)
    if request.method=='PUT':
        serializer=Card_serializer(card,data=request.data)
        if not (serializer.is_valid()):
            return Response (serializer.data,status=status.HTTP_400_BAD_REQUEST)
        if serializer.validated_data['manual_price']:
            if not serializer.validated_data['price']:
                return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer.validated_data['price']= (serializer.validated_data['hours_number']*serializer.validated_data['hour_price']) * (1 - (serializer.validated_data['discount']/100))    
        serializer.save()
        return Response (serializer.data,status=status.HTTP_201_CREATED)
    if request.method=='DELETE':
        card.is_deleted=True
        card.deleted_at=datetime.now()
        card.save()
        serializer=Card_serializer(card)
        return Response(status=status.HTTP_201_CREATED)

#Acitivity CRUD
@api_view(['GET','POST'])
def activity(request):
    if request.method=='GET':
        if not (activities := Activity.objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Activity_serializer(activities,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=Activity_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
def activity_edit(request,id):
    try:
        activity=Activity.objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method=='GET':
        serializer=Activity_serializer(activity)
        return Response (serializer.data,status=status.HTTP_200_OK)
    if request.method=='PUT':
        serializer=Activity_serializer(session,data=request.data)
        if not (serializer.is_valid()):
            return Response (serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response (serializer.data,status=status.HTTP_201_CREATED)
    if request.method=='DELETE':
        activity.is_deleted=True
        activity.deleted_at=datetime.now()
        activity.save()
        serializer=Activity_serializer(activity)
        return Response(status=status.HTTP_201_CREATED)


#Session CRUD
@api_view(['GET','POST'])
def session(request):
    if request.method=='GET':
        if not (sessions := Session.objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Session_serializer(sessions,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=Session_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
def session_edit(request,id):
    try:
        session=Session.objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method=='GET':
        serializer=Session_serializer(session)
        return Response (serializer.data,status=status.HTTP_200_OK)
    if request.method=='PUT':
        serializer=Session_serializer(session,data=request.data)
        if not (serializer.is_valid()):
            return Response (serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response (serializer.data,status=status.HTTP_201_CREATED)
    if request.method=='DELETE':
        session.is_deleted=True
        session.deleted_at=datetime.now()
        session.save()
        serializer=Session_serializer(session)
        return Response(status=status.HTTP_201_CREATED)

# Employee CRUD
@api_view(['GET','POST'])
def employee(request):
    if request.method=='GET':
        if not (employees := Employee.objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Employee_serializer(employees,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=Employee_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
def employee_edit(request,id):
    try:
        employee=Employee.objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method=='GET':
        serializer=Employee_serializer(employee)
        return Response (serializer.data,status=status.HTTP_200_OK)
    if request.method=='PUT':
        serializer=Employee_serializer(employee,data=request.data)
        if not (serializer.is_valid()):
            return Response (serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response (serializer.data,status=status.HTTP_201_CREATED)
    if request.method=='DELETE':
        employee.is_deleted=True
        employee.deleted_at=datetime.now()
        employee.save()
        serializer=Employee_serializer(employee)
        return Response(status=status.HTTP_201_CREATED)


# Employee CRUD
@api_view(['GET','POST'])
def car(request):
    if request.method=='GET':
        if not (cars := Car.objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Car_serializer(cars,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=Car_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
def car_edit(request,id):
    try:
        car=Car.objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method=='GET':
        serializer=Car_serializer(car)
        return Response (serializer.data,status=status.HTTP_200_OK)
    if request.method=='PUT':
        serializer=Car_serializer(car,data=request.data)
        if not (serializer.is_valid()):
            return Response (serializer.data,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response (serializer.data,status=status.HTTP_201_CREATED)
    if request.method=='DELETE':
        car.is_deleted=True
        car.deleted_at=datetime.now()
        car.save()
        serializer=Car_serializer(car)
        return Response(status=status.HTTP_201_CREATED)
