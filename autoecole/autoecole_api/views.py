from datetime import datetime
from multiprocessing.dummy import Manager
from autoecole_api.models import *
from autoecole_api.serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from autoecole_api.permissions import IsManager
from .tools import generete_username
from django.contrib.auth.hashers import make_password
import pandas as pd
from django.db.models import Q
from django.apps import apps
import json
# Custom JWT to obtain more information
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['fonction'] = user.fonction
        if user.fonction == 3:
            school=School.undeleted_objects.filter(owner=user.id).all()
            token['school'] = School_serializer(school, many=True).data

        if user.fonction == 1:
            token['school']=0

        # print(token)
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# School CRUD


@api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated, IsManager])
def school(request):
    # Get connected user

    if request.method == 'GET':
        # Get connected User
        user = request.user
        # Get list of school for connected user
        # school_id = Employee.undeleted_objects.filter(id=user.id).values('school_id')
        # if not (schools := Employee.undeleted_objects.filter(id=user.id).values('school_id')):
        if not (schools := School.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = School_serializer(schools, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        serializer = School_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def school_edit(request, id):
    try:
        school = School.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = School_serializer(school)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        serializer = School_serializer(school, data=request.data)
        if not (serializer.is_valid()):
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        school.is_deleted = True
        school.deleted_at = datetime.now()
        school.save()
        serializer = School_serializer(school)
        return Response(status=status.HTTP_201_CREATED)

# Student CRUD


@api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
def student(request,school_id):
    user = request.user
    if request.method == 'GET':
        if not (students := Student.undeleted_objects.filter(school=school_id)).all():
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Student_serializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        username_list=User.objects.values_list('username',flat=True)
        data=request.data.copy()
        data['created_by']=user.id
        data['fonction']=5
        data['school']=school_id
        data['username']=generete_username(data['first_name'], data['last_name'], username_list)
        data['password']='test'
        serializer = Student_serializer(data=data)
        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.error, status=status.HTTP_400_BAD_REQUEST)
        save_student=serializer.save()

        student=Student.undeleted_objects.filter(id=save_student.id).values_list('id',flat=True)
        employees=Employee.undeleted_objects.filter(school=school_id).values_list('id',flat=True)
        owners=School.undeleted_objects.filter(id=school_id).values_list('owner',flat=True)
        notification_users=list(employees) + list(owners) + list(student)

        #Save Notif
        save_notif=notification_db(notification_users,
                                'student','Add new student',
                                f'Student {save_student.first_name} {save_student.last_name} is added',
                                1)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
# @permission_classes([IsAuthenticated])
def student_edit(request, id):
    try:
        student = Student.undeleted_objects.get(id=id)
        #Get user notification
        employees=Employee.undeleted_objects.filter(school=student.school.id).values_list('id',flat=True)
        owners=School.undeleted_objects.filter(id=student.school.id).values_list('owner',flat=True)
        notification_users=list(employees) + list(owners)
        notification_users.append(student.id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)


    if request.method == 'GET':
        serializer = Student_serializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        serializer = Student_serializer(student, data=request.data)
        if not (serializer.is_valid()):
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        save_student=serializer.save()

        #Save Notif
        save_notif=notification_db(notification_users,
                                'student','Edit student',
                                f'Student {save_student.first_name} {save_student.last_name} edited',
                                1)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        student.is_deleted = True
        student.deleted_at = datetime.now()
        student.save()
        serializer = Student_serializer(student)

        #Save Notif
        save_notif=notification_db(notification_users,
                                'student','delete student',
                                f'Student {student.first_name} {student.last_name} deleted',
                                1)

        return Response(status=status.HTTP_201_CREATED)

# Card CRUD


@api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
def card(request,school_id,progress_status):
    if request.method == 'GET':
        status_list=[1,2,3,4,5,6]
        if progress_status == 'completed':
            status_list=[7]

        if not (cards := Card.undeleted_objects.filter(student__school=school_id).filter(status__in=status_list).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Card_serializer_read(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        serializer = Card_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST,)
        # if serializer.validated_data['manual_price']:
        #     if not serializer.validated_data['price']:
        #         return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     serializer.validated_data['price'] = (
        #         serializer.validated_data['hours_number']*serializer.validated_data['hour_price']) * (1 - (serializer.validated_data['discount']/100))
        obj=serializer.save()

        history_data={
                    'card':obj.id,
                    'status':1,
                    'date':datetime.now().date(),
                    'created_by':request.user.id
                    }
        serializer_history=Card_status_serializer(data=history_data)

        if not serializer_history.is_valid():
            return Response(serializer_history.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer_history.save()

        #Save Notif
            #get users
        employees=Employee.undeleted_objects.filter(school=school_id).values_list('id',flat=True)
        owners=School.undeleted_objects.filter(id=school_id).values_list('owner',flat=True)
        notification_users=list(employees) + list(owners)
        notification_users.append(obj.student.id)

        save_notif=notification_db(notification_users,
                                'card','Add new card',
                                f' new card for {obj.student.first_name} is added',
                                1)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
# @permission_classes([IsAuthenticated])
def card_edit(request, id):
    try:
        card = Card.undeleted_objects.get(id=id)
        #Save Notif
            #get users
        employees=Employee.undeleted_objects.filter(school=card.student.school.id).values_list('id',flat=True)
        owners=School.undeleted_objects.filter(id=card.student.school.id).values_list('owner',flat=True)
        notification_users=list(employees) + list(owners)
        notification_users.append(card.student.id)

    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Card_serializer_read(card)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        data=request.data.copy()
        if data['status'] != 99:
            data['end_at']=None
        serializer = Card_serializer(card, data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        save_card=serializer.save()

        #Save History
        try:
            history=CardStatusHistory.undeleted_objects.filter(card=id).latest("id")
            if history.status != card.status:
                history_data={
                    'card':id,
                    'status':card.status.id,
                    'date':datetime.now().date(),
                    'created_by':request.user.id
                }
                serializer_history=Card_status_serializer(data=history_data)

                if not serializer_history.is_valid():
                    return Response(serializer_history.errors, status=status.HTTP_400_BAD_REQUEST)

                serializer_history.save()

        except Exception:
            history_data={
                    'card':id,
                    'status':card.status.id,
                    'date':datetime.now().date(),
                    'created_by':request.user.id
                }
            serializer_history=Card_status_serializer(data=history_data)

            if not serializer_history.is_valid():
                return Response(serializer_history.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer_history.save()

        #Save notif
        save_notif=notification_db(notification_users,
                        'card','Update card',
                        f' Update card {save_card.student.first_name} number {save_card.id}',
                        1)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        card.is_deleted = True
        card.deleted_at = datetime.now()
        card.save()
        serializer = Card_serializer(card)

        #Save notif
        save_notif=notification_db(notification_users,
                'card','Delete card',
                f' Delete card {card.student.first_name} number {card.id}',
                1)

        return Response(status=status.HTTP_201_CREATED)

@api_view(['GET'])
def card_history(request, card_id):
        history=CardStatusHistory.undeleted_objects.filter(card=card_id).all()
        if not history:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer_history = Card_status_serializer_read(history,many=True)
        return Response(serializer_history.data, status=status.HTTP_200_OK)

# Acitivity CRUD
@api_view(['GET', 'POST'])
def activity(request):
    if request.method == 'GET':
        if not (activities := Activity.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Activity_serializer(activities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        serializer = Activity_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def activity_edit(request, id):
    try:
        activity = Activity.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Activity_serializer(activity)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        serializer = Activity_serializer(session, data=request.data)
        if not (serializer.is_valid()):
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        activity.is_deleted = True
        activity.deleted_at = datetime.now()
        activity.save()
        serializer = Activity_serializer(activity)
        return Response(status=status.HTTP_201_CREATED)


# Session CRUD
@api_view(['GET', 'POST'])
def session(request, school_id):
    if request.method == 'GET':
        if not (sessions := Session.undeleted_objects.filter(card__student__school=school_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Session_serializer_read(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        serializer = Session_serializer_edit(data=request.data)

        car=request.data['car']
        employee=request.data['employee']
        start_at=request.data['start_at']
        end_at=request.data['end_at']
        day=request.data['day']

        # Check the availability of the employee and the car for this session
        sessions=Session.undeleted_objects.filter(
            card__student__school=school_id,
            day=day,
            ).filter(
                Q(start_at__lt=end_at) & Q(end_at__gt=start_at)).filter(
                    Q(employee=employee) | Q(car=car))

        if sessions.count() > 0:
            return Response({'error':'session conflict'}, status=status.HTTP_400_BAD_REQUEST)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        save_session=serializer.save()

        #save notification
            #get users
        owners=School.undeleted_objects.filter(id=save_session.card.student.school.id).values_list('owner',flat=True)
        notification_users = list(owners)
        notification_users.append(save_session.employee.id)
        notification_users.append(save_session.card.student.id)

        save_notif=notification_db(notification_users,
                'session','Add new session',
                f'new session start at {save_session.day} {save_session.start_at} for card number {save_session.card.id} is added',2)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def card_session(request, card_id):
    if request.method == 'GET':
        if not (sessions := Session.undeleted_objects.filter(card=card_id).all()):
            print(sessions)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Session_serializer_read(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
def session_edit(request, id):
    try:
        session = Session.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Session_serializer_edit(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        car=request.data['car']
        employee=request.data['employee']
        start_at=request.data['start_at']
        end_at=request.data['end_at']
        day=request.data['day']

        # Check the availability of the employee and the car for this session
        sessions=Session.undeleted_objects.filter(
            card__student__school=session.card.student.school,
            day=day,
            ).filter(
                Q(start_at__lt=end_at) & Q(end_at__gt=start_at)).filter(
                    Q(employee=employee) | Q(car=car))

        if sessions.count() > 0:
            return Response({'error':'session conflict'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = Session_serializer_edit(session, data=request.data)
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        save_session = serializer.save()

        #save notification
            #get users
        owners=School.undeleted_objects.filter(id=save_session.card.student.school.id).values_list('owner',flat=True)
        notification_users = list(owners)
        notification_users.append(save_session.employee.id)
        notification_users.append(save_session.card.student.id)

        save_notif=notification_db(notification_users,
                'session','Edit session',
                f'The session number {session.id} is updated',2)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        session.is_deleted = True
        session.deleted_at = datetime.now()
        session.save()
        serializer = Session_serializer_edit(session)

        #save notification
            #get users
        owners=School.undeleted_objects.filter(id=session.card.student.school.id).values_list('owner',flat=True)
        notification_users = list(owners)
        notification_users.append(session.employee.id)
        notification_users.append(session.card.student.id)

        save_notif=notification_db(notification_users,
                'session','Delete session',
                f'The session number {session.id} is deleted',2)

        return Response(status=status.HTTP_201_CREATED)

# Employee CRUD


@api_view(['GET', 'POST'])
def employee(request,school_id):
    user=request.user
    if request.method == 'GET':
        if not (employees := Employee.undeleted_objects.filter(school=school_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Employee_serializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':

        username_list=User.objects.values_list('username',flat=True)
        data=request.data.copy()
        data['created_by']=user.id
        data['school']=school_id
        data['is_active']=True
        data['username']=generete_username(data['first_name'], data['last_name'], username_list)
        data['password']='test'

        serializer = Employee_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def employee_edit(request, id):
    user=request.user
    try:
        employee = Employee.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Employee_serializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        username_list=User.objects.values_list('username',flat=True)
        data=request.data.copy()
        data['updated_by']=user.id
        data['school']=employee.school.id
        first_name=employee.first_name
        last_name=employee.last_name
        if 'first_name' in data:
            first_name=data['first_name']

        if 'last_name' in data:
            last_name=data['last_name']

        data['username']=generete_username(first_name, last_name, username_list)
        data['password']=employee.password
        serializer = Employee_serializer(employee, data=data)
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        employee.is_deleted = True
        employee.deleted_at = datetime.now()
        employee.save()
        serializer = Employee_serializer(employee)
        return Response(status=status.HTTP_201_CREATED)


# Car CRUD
@api_view(['GET', 'POST'])
def car(request,school_id):
    user=request.user

    if request.method == 'GET':
        if not (cars := Car.undeleted_objects.filter(school=school_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Car_serializer(cars, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        data=request.data.copy()
        data['created_by']=user.id
        data['school']=school_id
        serializer = Car_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        #save notification
            #get users
        employees=Employee.undeleted_objects.filter(school=school_id).values_list('id',flat=True)
        owners=School.undeleted_objects.filter(id=school_id).values_list('owner',flat=True)
        notification_users=list(employees) + list(owners)
        save_notif=notification_db(notification_users,'car','new car','new car added', 1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def car_edit(request, id):
    try:
        car = Car.undeleted_objects.get(id=id)
        #save notification
            #get users
        employees=Employee.undeleted_objects.filter(school=car.school.id).values_list('id',flat=True)
        owners=School.undeleted_objects.filter(id=car.school.id).values_list('owner',flat=True)
        notification_users=list(employees) + list(owners)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Car_serializer(car)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        data=request.data.copy()
        data['school']=car.school.id
        serializer = Car_serializer(car, data=data)
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        #save notif
        save_notif=notification_db(notification_users,'car','edit car',f'Car {car.marque} {car.model} edited', 1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        car.is_deleted = True
        car.deleted_at = datetime.now()
        car.save()
        serializer = Car_serializer(car)

        #save notif
        save_notif=notification_db(notification_users,'car','Delete car',f'Car {car.marque} {car.model} deleted', 1)
        return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
def licence(request):
    if request.method == 'GET':
        if not (licences := LicenceType.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Licence_serializer(licences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def status_status(request):
    if request.method == 'GET':
        if not (status_status_data := Status.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Status_serializer(status_status_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def owner(request):
    if request.method == 'GET':
        if not (owner := Owner.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Owner_serializer(owner, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def session_types(request):
    if request.method == 'GET':
        if not (session_types := SessionType.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = SessionTypes_serializer(session_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        owner_data = dict()
        school_data = dict()
        username_list = User.objects.values_list('username',flat=True)
        data = request.data.copy()

        #Format owner data
        owner_data['fonction']=3
        owner_data['first_name'] = data['first_name']
        owner_data['last_name'] = data['last_name']
        owner_data['tel'] = data['tel']
        owner_data['password'] =  make_password(data['password'])
        owner_data['username'] = generete_username(owner_data['first_name'], owner_data['last_name'],username_list)
        owner_serializer = Owner_serializer(data=owner_data)

        #Save Owner Model
        if not owner_serializer.is_valid():
            return Response(owner_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        owner_serializer.save()

        #Format school data
        school_data['name']=data['name']
        school_data['code']=data['code']
        school_data['owner']=owner_serializer.data['id']
        school_serializer = School_serializer(data=school_data)
        #Save School Model
        if not school_serializer.is_valid():
            Owner.objects.filter(id=owner_serializer.data['id']).delete()
            return Response(school_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        school_serializer.save()

    return Response(owner_serializer.data, status=status.HTTP_200_OK)


def notification_db(users:list,module:str,title:str,text:str,notifcation_type:str)->bool:
    """Save notification to DB

    Args:
        users (list): list of users
        text (str): notification text
        notifcation_type (str): notification type

    Returns:
        bool: True if successfully saved to DB
    """
    notication_data={
    'user':'',
    'notification_type': notifcation_type,
    'module':module,
    'title':title.capitalize(),
    'message':text.capitalize()
    }
    for user in users:
        notication_data['user']=user
        notification_serializer=Notification_serializer(data=notication_data)

        if not notification_serializer.is_valid():
            return (notification_serializer.errors)

        notification_serializer.save()

    return True

@api_view(['PUT'])
def read_notification(request, id):
    if request.method == 'PUT':
        try:
            notification = Notification.undeleted_objects.get(id=id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        notification.is_read=True
        notification.save()
        serializer=Notification_serializer_read(notification)
        return Response (serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_notification(request, id):
    if request.method == 'DELETE':
        try:
            notification = Notification.undeleted_objects.get(id=id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        notification.is_deleted=True
        notification.save()
        serializer=Notification_serializer_read(notification)
        return Response (serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification(request):
    if request.method == 'GET':
        notifications = Notification.undeleted_objects.filter(user=request.user).all()
        serializer=Notification_serializer_read(notifications,many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

# Employee CRUD
@api_view(['GET'])
def stats(request, school_id):
    stats=dict()
    card_stat=dict()
    students_stat=dict()
    cards=Card.undeleted_objects.filter(student__school=school_id).values()
    df_card=pd.DataFrame(cards)
    if df_card.size > 0:
        df_cards_inprogress=df_card[df_card["status_id"] == 1]
        df_cards_completed=df_card[df_card["status_id"] == 2]
        df_cards_canceled=df_card[df_card["status_id"] == 3]
        card_stat["cards_count"]=len(df_card)
        card_stat["count_cards_inprogress"]=len(df_cards_inprogress)
        card_stat["count_cards_completed"]=len(df_cards_completed)
        card_stat["count_cards_canceled"]=len(df_cards_canceled)

    else:
        card_stat["cards_count"]=0
        card_stat["count_cards_inprogress"]=0
        card_stat["count_cards_completed"]=0
        card_stat["count_cards_canceled"]=0

    students=Student.undeleted_objects.filter(school=school_id).values()
    df_students=pd.DataFrame(students)
    students_stat['students_count']=len(df_students)


    stats.update(card_stat)
    stats.update(students_stat)


    return Response(stats,status=status.HTTP_200_OK)


# Payment CRUD
@api_view(['GET', 'POST'])
def payment(request,school_id):
    user=request.user

    if request.method == 'GET':
        if not (payments := Payment.undeleted_objects.filter(card__student__school=school_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Payments_serializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        data=request.data.copy()
        data['created_by']=user.id
        serializer = Payments_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        save_payement=serializer.save()

        #Save nofications
        owners=School.undeleted_objects.filter(id=save_payement.card.student.school.id).values_list('owner',flat=True)
        notification_users= list(owners)
        notification_users.append(save_payement.card.student.id)

        #Save Notif
        save_notif=notification_db(notification_users,
                                'payment','Add new payment',
                                f'Add new payment for card number {save_payement.card.id}',
                                2)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
def payment_edit(request,id):
    try:
        payment = Payment.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = Payments_serializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = Payments_serializer(payment,data=request.data)
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        save_payement=serializer.save()

        #Save nofications
        owners=School.undeleted_objects.filter(id=save_payement.card.student.school.id).values_list('owner',flat=True)
        notification_users= list(owners)
        notification_users.append(save_payement.card.student.id)

        #Save Notif
        save_notif=notification_db(notification_users,
                                'payment','Edit payment',
                                f'Edit payment number {save_payement.id} for card number {save_payement.card.id}',
                                1)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        payment.is_deleted = True
        payment.deleted_at = datetime.now()
        payment.save()
        serializer = Payments_serializer(payment)

        #Save nofications
        owners=School.undeleted_objects.filter(id=payment.card.student.school.id).values_list('owner',flat=True)
        notification_users= list(owners)
        notification_users.append(payment.card.student.id)

        #Save Notif
        save_notif=notification_db(notification_users,
                                'payment','Delete payment',
                                f'delete payment number {payment.id}  for card number {payment.card.id}',
                                2)
        return Response(status=status.HTTP_201_CREATED)


# Payment CRUD
@api_view(['GET', 'POST'])
def payment_dossier(request,card_id):
    if request.method == 'GET':
        if not (payments := Payment.undeleted_objects.filter(card=card_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Payments_serializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
