from datetime import datetime, date, timedelta
from multiprocessing.dummy import Manager
from autoecole_api.models import *
from autoecole_api.serializers import *
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from autoecole_api.permissions import IsManager
from .tools import generete_username
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
import pandas as pd
from django.db.models import Q
from django.apps import apps
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .services import create_notification_with_deliveries
from .notifications.dispatcher import send_pending_deliveries_for_notification
# Custom JWT to obtain more information

def get_user_role(number):
    USER_TYPE_CHOICES = (
        (1, 'Guest'),
        (2, 'Admin'),
        (3, 'Owner'),
        (4, 'Trainer'),
        (5, 'Student'),
        )
    for num, name in USER_TYPE_CHOICES:
        if num == number:
            return name
    return None

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    tel = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprime 'username' hérité
        self.fields.pop('username', None)

    def validate(self, attrs):
        tel = attrs.get('tel')
        password = attrs.get('password')

        # Authentifier avec téléphone au lieu de username/email
        user = authenticate(request=self.context.get('request'),
                            tel=tel, password=password)

        if not user:
            raise serializers.ValidationError('Numéro de téléphone ou mot de passe incorrect.')

        # Générer le token
        refresh = self.get_token(user)

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        # Claims personnalisés
        data['tel'] = user.tel
        data['email'] = user.email
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['fonction'] = user.fonction
        data['role'] = get_user_role(user.fonction)

        if user.fonction == 3:
            school = School.undeleted_objects.get(owner=user.id)
            data['school'] = School_serializer(school).data
        elif user.fonction == 1:
            data['school'] = 0
        elif user.fonction == 5:
            user = Student.undeleted_objects.get(id=user.id)
            data['school'] = School_serializer(user.school).data

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['tel'] = user.tel
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['fonction'] = user.fonction
        token['role'] = get_user_role(user.fonction)

        if user.fonction == 3:
            school = School.undeleted_objects.filter(owner=user.id).all()
            token['school'] = School_serializer(school, many=True).data
        elif user.fonction == 1:
            token['school'] = 0

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# School CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsManager])
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
@permission_classes([IsAuthenticated, IsManager])
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
@permission_classes([IsAuthenticated])
def student(request,school_id):
    user = request.user
    if request.method == 'GET':
        if not (students := Student.undeleted_objects.filter(school=school_id)).all():
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Student_serializer_read(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        username_list=User.objects.values_list('username',flat=True)
        new_data=dict(request.data['student'])

        if 'avatar' in request.FILES:
            new_data['avatar'] = request.FILES['avatar']

        new_data['school']=student.school.id
        new_data['is_active']=student.is_active

        first_name=student.first_name
        last_name=student.last_name
        if 'first_name' in new_data:
            first_name=new_data['first_name'][0]

        if 'last_name' in new_data:
            last_name=new_data['last_name'][0]

        new_data['username']=generete_username(first_name, last_name, username_list)
        new_data['password']=student.password
        for key in new_data:
            if isinstance(new_data[key], list) and len(new_data[key]) == 1:
                new_data[key] = new_data[key][0]

        serializer = Student_serializer(student, data=new_data, context={'request': request})
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
@parser_classes([MultiPartParser, FormParser])  # ✅ Pour gérer multipart/form-data
@permission_classes([IsAuthenticated])
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
        serializer = Student_serializer_read(student, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        username_list=User.objects.values_list('username',flat=True)
        new_data=dict(request.data)

        if 'avatar' in request.FILES:
            new_data['avatar'] = request.FILES['avatar']

        new_data['school']=student.school.id
        new_data['is_active']=student.is_active

        first_name=student.first_name
        last_name=student.last_name
        if 'first_name' in new_data:
            first_name=new_data['first_name'][0]

        if 'last_name' in new_data:
            last_name=new_data['last_name'][0]

        new_data['username']=generete_username(first_name, last_name, username_list)
        new_data['password']=student.password
        for key in new_data:
            if isinstance(new_data[key], list) and len(new_data[key]) == 1:
                new_data[key] = new_data[key][0]

        serializer = Student_serializer(student, data=new_data, context={'request': request})
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        obj=serializer.save()

        #Save nofications
        #get users
        student = obj
        audiance = []
        if id != request.user.id:
            audiance.append(student)
        print('audiance', audiance)
        push_notification_to_users(
            audiance,
            'Générique',
            'student',
            'Profil modifié 📝',
            f'Des informations ont été modifiées pour votre profil',
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        student.is_deleted = True
        student.deleted_at = datetime.now()
        student.save()
        serializer = Student_serializer(student)
        cards=Card.undeleted_objects.filter(student=id).all()
        for card in cards:
            card.is_deleted= True
            card.save()
        #Save Notif
        save_notif=notification_db(notification_users,
                                'student','delete student',
                                f'Student {student.first_name} {student.last_name} deleted',
                                1)

        return Response(status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def student_reset_password(request, id):
    try:
        student = Student.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PUT':
        ##Send mail to student
        serializer = Student_serializer(student)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def student_enable_disable_account(request, id):
    try:
        student = Student.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PUT':
        account_status=student.is_active
        student.is_active= not account_status
        student.save()

        serializer = Student_serializer(student)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


# Card CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def card(request,school_id,progress_status):
    if request.method == 'GET':
        cards=None
        if progress_status == 'completed':
            #Filter all cards with status equal to completed ( status id 99)
            cards = Card.undeleted_objects.filter(student__school=school_id).filter(status=99).all()
        else:
            #Filter all cards with status Not equal to completed ( status id 99)
            cards = Card.undeleted_objects.filter(student__school=school_id).filter(~Q(status = 99)).all()

        if request.user.fonction == 5:
            # If user is student, filter cards by student id
            cards = cards.filter(student=request.user.id)

        if not cards:
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

        #Save nofications
        #get users
        student = obj.student
        owner = obj.student.school.owner
        audiance = []
        audiance.append(student)
        if owner.id != request.user.id:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Générique',
            'card',
            'Nouveau dossier créé 🗂️',
            f'Un nouveau dossier a été créé pour {obj.student.first_name} {obj.student.last_name}',
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])  # ✅ Pour gérer multipart/form-data
@permission_classes([IsAuthenticated])
def save_card_and_student(request, school_id):
    if request.method == 'POST':
        username_list=User.objects.values_list('username',flat=True)
        data = request.data

        # Séparer les champs student_ et dossier_
        student_data = {}
        dossier_data = {}

        for key, value in data.items():
            if key.startswith('dossier_'):
                dossier_key = key.replace('dossier_', '')
                dossier_data[dossier_key] = value
            if key.startswith('student_'):
                student_key = key.replace('student_', '')
                student_data[student_key] = value


        if 'avatar' in request.FILES:
            student_data['avatar'] = request.FILES['avatar']

        student_data['school']=school_id
        first_name=student_data['first_name'][0]
        last_name=student_data['last_name'][0]
        student_data['fonction'] = 5 #For student

        student_data['username']=generete_username(first_name, last_name, username_list)
        student_data['password']='test'
        for key in student_data:
            if isinstance(student_data[key], list) and len(student_data[key]) == 1:
                student_data[key] = student_data[key][0]
        serializer = Student_serializer(data=student_data, context={'request': request})
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        save_student=serializer.save()

        data_card = dossier_data
        data_card['student'] = save_student.id
        data_card['manual_price'] = False
        serializer = Card_serializer(data=data_card)
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

        #Save nofications
        #get users
        student = obj.student
        owner = obj.student.school.owner
        audiance = []
        audiance.append(student)
        if owner.id != request.user.id:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Générique',
            'card',
            'Nouveau dossier créé 🗂️',
            f'Un nouveau dossier a été créé pour {obj.student.first_name} {obj.student.last_name}',
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)



@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
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

        obj=serializer.save()

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

        #Save nofications
        #get users
        student = obj.student
        owner = obj.student.school.owner
        audiance = []
        audiance.append(student)
        if owner.id != request.user.id:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Générique',
            'card',
            'Dossier modifié 🗂',
            f'Le dossier numéro {card.id} de {obj.student.first_name} {obj.student.last_name} a été modifié',
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        card.is_deleted = True
        card.deleted_at = datetime.now()
        card.save()
        serializer = Card_serializer(card)

        #Save nofications
        #get users
        student = card.student
        owner = card.student.school.owner
        audiance = []
        audiance.append(student)
        if owner.id != request.user.id:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Générique',
            'card',
            'Dossier supprimé 🚮',
            f'Le dossier numéro {card.id} de {card.student.first_name} {card.student.last_name} a été supprimé',
        )

        return Response(status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def card_history(request, card_id):
        history=CardStatusHistory.undeleted_objects.filter(card=card_id).all()
        if not history:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer_history = Card_status_serializer_read(history,many=True)
        return Response(serializer_history.data, status=status.HTTP_200_OK)

# Acitivity CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def session(request, school_id):
    if request.method == 'GET':
        sessions = Session.undeleted_objects.filter(employee__school=school_id).all()
        if get_user_role(request.user.fonction) == 'Student':
            # If user is student, filter sessions by student id
            sessions = sessions.filter(card__student=request.user.id)
        if not sessions:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Session_serializer_read(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = Session_serializer_edit(data=request.data)

        event_type = request.data.get('event_type')
        car = request.data.get('car')
        employee = request.data.get('employee')
        card = request.data.get('card')  # facultatif selon le type d'événement
        start_at = request.data.get('start_at')
        end_at = request.data.get('end_at')
        day = request.data.get('day')

        # Vérification des conflits si les champs de base sont présents
        if start_at and end_at and day:
            conflict_filter = Q(day=day) & Q(start_at__lt=end_at) & Q(end_at__gt=start_at)
            resource_conflict = Q()

            if employee:
                resource_conflict |= Q(employee=employee)
            if car:
                resource_conflict |= Q(car=car)
            if card:
                resource_conflict |= Q(card=card)

            if resource_conflict:  # On vérifie uniquement si au moins une ressource est fournie
                conflicting_sessions = Session.undeleted_objects.filter(
                    conflict_filter & resource_conflict
                )
                if conflicting_sessions.exists():
                    return Response(
                        {'error': 'event conflict: at least one resource (employee, car, or student) is already booked at this time'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        save_session = serializer.save()

        # Notifications uniquement pour les sessions
        if event_type == 'session':
            owners = School.undeleted_objects.filter(
                id=save_session.card.student.school.id
            ).values_list('owner', flat=True)

            notification_users = list(owners)
            notification_users.append(save_session.employee.id)
            notification_users.append(save_session.card.student.id)

            notification_db(
                notification_users,
                'session',
                'Add new session',
                f'New session starting at {save_session.day} {save_session.start_at} for card number {save_session.card.id} has been added',
                2
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def week_sessions(request, school_id):

    #Get Week start and end days
    # Date d'aujourd'hui
    today = date.today()
    week_days = today.weekday()
    week_first_day = today - timedelta(days=week_days)
    week_last_day = week_first_day + timedelta(days=6)
    sessions = Session.undeleted_objects.filter(employee__school=school_id).filter(day__gte=week_first_day, day__lte=week_last_day).all()
    if get_user_role(request.user.fonction) == 'Student':
        # If user is student, filter sessions by student id
        sessions = sessions.filter(card__student=request.user.id)
    if not sessions:
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = Session_serializer_read(sessions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def card_session(request, card_id):
    if request.method == 'GET':
        if not (sessions := Session.undeleted_objects.filter(card=card_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Session_serializer_read(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def session_edit(request, id):
    try:
        session = Session.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Session_serializer_edit(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        serializer = Session_serializer_edit(session, data=request.data)

        event_id = id  # ID de l'événement en cours d'édition (obligatoire pour exclure self)

        event_type = request.data.get('event_type')
        car = request.data.get('car')
        employee = request.data.get('employee')
        card = request.data.get('card')  # facultatif pour type "Autres"
        start_at = request.data.get('start_at')
        end_at = request.data.get('end_at')
        day = request.data.get('day')

        # Vérification des conflits uniquement si date/heure présentes
        if start_at and end_at and day:
            conflict_filter = Q(day=day) & Q(start_at__lt=end_at) & Q(end_at__gt=start_at)
            resource_conflict = Q()

            if employee:
                resource_conflict |= Q(employee=employee)
            if car:
                resource_conflict |= Q(car=car)
            if card:
                resource_conflict |= Q(card=card)

            if resource_conflict:
                conflicting_sessions = Session.undeleted_objects.filter(
                    conflict_filter & resource_conflict
                ).exclude(id=event_id)  # exclure l'événement qu'on modifie

                if conflicting_sessions.exists():
                    return Response(
                        {'error': 'event conflict: at least one resource (employee, car, or student) is already booked at this time'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        save_session = serializer.save()

        # Notification uniquement si c'est une session
        if event_type == 'session':
            owners = School.undeleted_objects.filter(
                id=save_session.card.student.school.id
            ).values_list('owner', flat=True)

            notification_users = list(owners)
            notification_users.append(save_session.employee.id)
            notification_users.append(save_session.card.student.id)

            notification_db(
                notification_users,
                'session',
                'Session updated',
                f'Session updated for card number {save_session.card.id} on {save_session.day} at {save_session.start_at}',
                2
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

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
@permission_classes([IsAuthenticated])
def employee(request,school_id):
    user=request.user
    if request.method == 'GET':
        if not (employees := Employee.undeleted_objects.filter(school=school_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Employee_serializer_read(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        username_list=User.objects.values_list('username',flat=True)
        data=request.data.copy()
        employee_data = {}
        for key, value in data.items():
            if key.startswith('student_'):
                student_key = key.replace('student_', '')
                employee_data[student_key] = value

        if 'avatar' in request.FILES:
            employee_data['avatar'] = request.FILES['avatar']

        employee_data['created_by']=user.id
        employee_data['school']=school_id
        employee_data['is_active']=True
        # Conversion en objet datetime
        dt = datetime.strptime(employee_data['birthday'], "%Y-%m-%dT%H:%M:%S.%fZ")
        employee_data['birthday'] = dt.strftime("%Y-%m-%d")
        
        employee_data['username']=generete_username(employee_data['first_name'][0], employee_data['last_name'][0], username_list)
        employee_data['password']='test'
        employee_data['fonction'] = 4 #trainer
        serializer = Employee_serializer(data=employee_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def employee_edit(request, id):
    user=request.user
    try:
        employee = Employee.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Employee_serializer_read(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        username_list=User.objects.values_list('username',flat=True)
        data=request.data.copy()
        employee_data = {}
        for key, value in data.items():
            if key.startswith('student_'):
                student_key = key.replace('student_', '')
                employee_data[student_key] = value

        if 'avatar' in request.FILES:
            employee_data['avatar'] = request.FILES['avatar']
        employee_data['updated_by']=user.id
        employee_data['school']=employee.school.id
        employee_data['username']=employee.username
        employee_data['password']=employee.password
        employee_data['is_active']=employee.is_active
        dt = datetime.strptime(employee_data['birthday'], "%Y-%m-%dT%H:%M:%S.%fZ")
        employee_data['birthday'] = dt.strftime("%Y-%m-%d")

        serializer = Employee_serializer(employee, data=employee_data)
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def licence(request):
    if request.method == 'GET':
        if not (licences := LicenceType.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Licence_serializer(licences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def status_status(request):
    if request.method == 'GET':
        if not (status_status_data := Status.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Status_serializer(status_status_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
        owner_data['fonction']=3  # For owner
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
        school_data['name']=data['school_name']
        school_data['code']=data['school_code']
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


def push_notification_to_users(audiance, notification_type,module, title, message):

    try:
        notification_type = NotificationType.objects.get(title=notification_type)
        for user in audiance:
            notification = create_notification_with_deliveries(
                user=user,
                notification_type=notification_type,
                module=module,
                title=title,
                message=message
            )

            send_pending_deliveries_for_notification(notification)

        return True

    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_notification(request, id):
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
@permission_classes([IsAuthenticated])
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
        # notifications = Notification.undeleted_objects.filter(user=request.user).all()
        notifications = Notification.undeleted_objects.all()
        if get_user_role(request.user.fonction) == 'Student':
            # If user is student, filter notifications by student id
            notifications = notifications.filter(user=request.user.id)

        if not notifications:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Notification_serializer_read(notifications,many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

# Employee CRUD
@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
        student = save_payement.card.student
        owner = save_payement.card.student.school.owner
        audiance = []
        audiance.append(student)
        if owner.id != request.user.id:
            audiance.append(owner)

        print('audiance',set(audiance))
        push_notification_to_users(
            audiance,
            'Générique',
            'payment',
            'Nouveau Payment 💰',
            f'Un payement de {save_payement.amount} a été effectué pour la carte {save_payement.card.id}.'
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
@permission_classes([IsAuthenticated])
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
        # Prepare notification data
        student = save_payement.card.student
        owner = save_payement.card.student.school.owner
        audiance = []
        audiance.append(student)
        if owner.id != request.user.id:
            audiance.append(owner)
        push_notification_to_users(
            audiance,
            'Générique',
            'payment',
            'Payment modifié 💰',
            f'le payement de {save_payement.amount} a été modifié pour la carte {save_payement.card.id}.'
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        payment.is_deleted = True
        payment.deleted_at = datetime.now()
        payment.save()
        serializer = Payments_serializer(payment)

        #Save nofications
        # Prepare notification data
        save_payement = (Payment.undeleted_objects
                        .select_related(
                            "card__student__user_ptr",
                        )
                        .get(pk=id))
        student = save_payement.card.student
        owner = save_payement.card.student.school.owner
        audiance = []
        audiance.append(student)
        if owner.id != request.user.id:
            audiance.append(owner)
        push_notification_to_users(
            audiance,
            'Générique',
            'payment',
            'Payment supprimé 🚮',
            f'le payement de {save_payement.amount} a été supprimé pour la carte {save_payement.card.id}.'
        )
        return Response(status=status.HTTP_201_CREATED)


# Payment CRUD
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_dossier(request,card_id):
    if request.method == 'GET':
        if not (payments := Payment.undeleted_objects.filter(card=card_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Payments_serializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def countries(request):
    if request.method == 'GET':
        if not (countries := Country.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Country_serializer(countries, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def governorates(request, id):
    if request.method == 'GET':
        if not (governorates := Governorate.undeleted_objects.filter(country=id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Governorate_serializer(governorates, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cities(request, id):
    if request.method == 'GET':
        #if not (cities := City.undeleted_objects.filter(governorate=id).all()):
            # return Response(status=status.HTTP_204_NO_CONTENT)
        # serializer = City_serializer(cities, many=True)

        #This is a temporary fix to get all governorates for country with id=1
        if not (governorates := Governorate.undeleted_objects.filter(country=1).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Governorate_serializer(governorates, many=True)
    
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET','PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    # (1, 'Guest'),
    # (2, 'Admin'),
    # (3, 'Owner'),
    # (4, 'Trainer'),
    # (5, 'Student'),
    try:
        user_fonction=request.user.fonction
        user_id=request.user.id
        print('user_fonction',user_fonction)



    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if user_fonction in [1, 2]: #Guest and Admin
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user_fonction == 3: #Owner
            try:
                profile = Owner.undeleted_objects.get(id=user_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            profile_serialzer=Owner_serializer_read(profile)

        if user_fonction == 4: #Trainer
            try:
                profile = Employee.undeleted_objects.get(id=user_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            profile_serialzer=Employee_serializer_read(profile)

        if user_fonction == 5: #Student
            try:
                profile = Student.undeleted_objects.get(id=user_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)
            profile_serialzer=Student_serializer_read(profile)
            print('profile', profile_serialzer.data)
        
        return Response(profile_serialzer.data, status=status.HTTP_200_OK)
    
    if request.method == 'PUT':
        if user_fonction in [1, 2]: #Guest and Admin
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user_fonction == 3: #Owner
            try:
                profile = Owner.undeleted_objects.get(id=user_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            profile_serialzer=Owner_serializer(profile)

        if user_fonction == 4: #Trainer
            try:
                profile = Employee.undeleted_objects.get(id=user_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            profile_serialzer=Employee_serializer(profile)

        if user_fonction == 5: #Student
            try:
                profile = Student.undeleted_objects.get(id=user_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            profile_serialzer=Student_serializer(profile)
        data=request.data.copy()
        profile_data = {}
        for key, value in data.items():
            if key.startswith('student_'):
                student_key = key.replace('student_', '')
                profile_data[student_key] = value

        if 'avatar' in request.FILES:
            profile_data['avatar'] = request.FILES['avatar']

        profile_data['updated_by']=user_id

        if user_fonction not in [1,2,3]: # Admin Guest and Owner doesn't have school 
            profile_data['school']=profile.school.id

        profile_data['username']=profile.username
        profile_data['password']=profile.password
        profile_data['is_active']=profile.is_active
        dt = datetime.strptime(profile_data['birthday'], "%Y-%m-%dT%H:%M:%S.%fZ")
        profile_data['birthday'] = dt.strftime("%Y-%m-%d")

        if user_fonction in [1, 2]: #Guest and Admin
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user_fonction == 3: #Owner
            serializer=Owner_serializer(profile, data=profile_data)
        if user_fonction == 4: #Trainer)
            serializer=Employee_serializer_read(profile, data=profile_data)
        if user_fonction == 5: #Student
            serializer=Student_serializer(profile, data=profile_data)

        if not (serializer.is_valid()):
            print('error profile', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    


#Notification PUSH
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def device_register(request):
    ser = DeviceRegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data
    _, created = Device.objects.update_or_create(
        token=d["token"],
        defaults={
            "user": request.user,
            "provider": d.get("provider", "expo"),  # ← NEW (par défaut Expo)
            "platform": d["platform"],
            "app_version": d.get("app_version", ""),
            "locale": d.get("locale", ""),
            "is_active": True,
        },
    )
    return Response({"created": created}, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def device_unregister(request):
    ser = DeviceUnregisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    token = ser.validated_data["token"]

    # On désactive seulement le device de l’utilisateur courant
    updated = Device.objects.filter(user=request.user, token=token).update(is_active=False)
    if updated == 0:
        # rien trouvé (token inconnu ou appartient à un autre user)
        return Response({"detail": "Token introuvable pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def device_ping(request):
    ser = DevicePingSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    qs = Device.objects.filter(user=request.user, is_active=True)
    if "token" in d and d["token"]:
        qs = qs.filter(token=d["token"])

    if not qs.exists():
        return Response({"detail": "Aucun device correspondant."}, status=status.HTTP_404_NOT_FOUND)

    updates = {"last_seen": timezone.now()}
    if "app_version" in d:
        updates["app_version"] = d["app_version"]
    if "locale" in d:
        updates["locale"] = d["locale"]

    qs.update(**updates)  # update() met bien à jour last_seen ici
    return Response(status=status.HTTP_204_NO_CONTENT)

User = get_user_model()
@api_view(["POST"])
@permission_classes([IsAuthenticated])  # adapte si besoin
def notification_create(request):
    ser = NotificationCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    v = ser.validated_data

    user = get_object_or_404(User, pk=v["user_id"])
    ntype = get_object_or_404(NotificationType, pk=v["notification_type_id"])

    notif = create_notification_with_deliveries(
        user=user,
        notification_type=ntype,
        module=v["module"],
        title=v["title"],
        message=v["message"],
        data=v.get("data"),
        priority=v.get("priority", "normal"),
        category=v.get("category", ""),
    )
    return Response(Notification_serializer(notif).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_send(request):
    ser = NotificationSendSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    notif_id = ser.validated_data["notification_id"]

    # Vérifie que la notif existe (et appartient bien à quelqu'un)
    get_object_or_404(Notification, pk=notif_id)

    stats = send_pending_deliveries_for_notification(notif_id)
    return Response({"notification_id": notif_id, "stats": stats}, status=status.HTTP_200_OK)