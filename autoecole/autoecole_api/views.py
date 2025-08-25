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
from autoecole_api.permissions import IsManager, IsPaymentDone
from .tools import generete_username, generete_password, get_user_role, generete_username
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
from django.db.models import F

# Custom JWT to obtain more information
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprime 'username' hérité
        self.fields.pop('username', None)

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')

        # Authentifier avec téléphone au lieu de username/email
        user = authenticate(request=self.context.get('request'),
                            phone=phone, password=password)

        if not user:
            raise serializers.ValidationError('Numéro de téléphone ou mot de passe incorrect.')

        # Générer le token
        refresh = self.get_token(user)

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        # Claims personnalisés
        data['phone'] = user.phone
        data['email'] = user.email
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['role'] = get_user_role(user.role)
        # school = User.undeleted_objects.get(id=user.id).school
        school = UserPreference.undeleted_objects.get(user=user.id).school
        data['school'] = School_serializer(school).data
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['phone'] = user.phone
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['role'] = get_user_role(user.role)
        school = UserPreference.undeleted_objects.get(user=user.id).school
        token['school'] = School_serializer(school).data

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def user(request, school_id):
    if request.method == 'GET':
        users = User.undeleted_objects.filter(school = school_id).all()
        if not users:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = User_serializer_read(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def user_preference(request):
    try:
        preferences = UserPreference.undeleted_objects.filter(user=request.user.id).first()
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        if not preferences:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = User_Preference_serializer_read(preferences)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        print('data', request.data)
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = User_Preference_serializer(preferences, data=data)
        if not (serializer.is_valid()):
            print("errors", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def school_preference(request):
    # schools = User.undeleted_objects.filter(phone=request.user.phone).all()
    schools = (
    User.undeleted_objects
        .filter(phone=request.user.phone)
        .values("school__id", "school__name")
    )
    if not schools:
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(list(schools), status=status.HTTP_200_OK)

# School CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsManager, IsPaymentDone])
def school(request):
    # Get connected user

    if request.method == 'GET':
        # Get connected User
        user = request.user
        # Get list of school for connected user
        # school_id = User.undeleted_objects.filter(id=user.id).values('school_id')
        # if not (schools := User.undeleted_objects.filter(id=user.id).values('school_id')):
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
@permission_classes([IsAuthenticated, IsManager, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
def student(request,school_id):
    user = request.user
    if request.method == 'GET':
        if not (students := User.undeleted_objects.filter(school=school_id, role=5)).all():
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = User_serializer_read(students, many=True)
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

        serializer = User_serializer(student, data=new_data, context={'request': request})
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        save_student=serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])  # ✅ Pour gérer multipart/form-data
@permission_classes([IsAuthenticated, IsPaymentDone])
def student_edit(request, id):
    try:
        student = User.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)


    if request.method == 'GET':
        serializer = User_serializer_read(student, context={'request': request})
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

        serializer = User_serializer(student, data=new_data, context={'request': request})
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
            'Activity',
            'student',
            'Profil modifié 📝',
            f'Des informations ont été modifiées pour votre profil',
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        student.is_deleted = True
        student.deleted_at = datetime.now()
        student.save()
        serializer = User_serializer(student)
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
@permission_classes([IsAuthenticated, IsPaymentDone])
def student_reset_password(request, id):
    try:
        student = Student.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PUT':
        ##Send mail to student
        serializer = User_serializer(student)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def enable_disable_account(request, id):
    try:
        user = User.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PUT':
        account_status=user.is_active
        user.is_active= not account_status
        user.save()

        serializer = User_serializer_read(user)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def enable_disable_car(request, id):
    try:
        car = Car.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PUT':
        car_status=car.is_active
        car.is_active= not car_status
        car.save()
        serializer = Car_serializer(car)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


# Card CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def card(request,school_id,progress_status):
    if request.method == 'GET':
        cards=None
        if progress_status == 'completed':
            #Filter all cards with status equal to completed ( status id 99)
            cards = Card.undeleted_objects.filter(school=school_id).filter(status=99).all()
        else:
            #Filter all cards with status Not equal to completed ( status id 99)
            cards = Card.undeleted_objects.filter(school=school_id).filter(~Q(status = 99)).all()

        if get_user_role(request.user.role) == 'Student':
            # If user is student, filter cards by student id
            cards = cards.filter(student__phone=request.user.phone)

        if not cards:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Card_serializer_read(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
        data = request.data.copy()
        data['school'] = school_id
        serializer = Card_serializer(data=data)
        if not serializer.is_valid():
            print('error', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST,)
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
        owner = User.undeleted_objects.filter(school=student.school.id, role=3).first()  # Get the owner of the school
        audiance = []
        audiance.append(student)
        if owner and owner != request.user:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Activity',
            'card',
            'Nouveau dossier créé 🗂️',
            f'Un nouveau dossier a été créé pour {obj.student.first_name} {obj.student.last_name}',
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])  # ✅ Pour gérer multipart/form-data
@permission_classes([IsAuthenticated, IsPaymentDone])
def save_card_and_student(request, school_id):
    if request.method == 'POST':
        data = request.data
        #Préparer les données
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

        # Vérifier si les champs requis sont présents
        if 'avatar' in request.FILES:
            student_data['avatar'] = request.FILES['avatar']
        
        #Save student
        student_data['school']=school_id
        first_name=student_data['first_name'][0]
        student_data['role'] = 5 #For student
        student_data['username']=generete_username(first_name)
        password = generete_password()


        for key in student_data:
            if isinstance(student_data[key], list) and len(student_data[key]) == 1:
                student_data[key] = student_data[key][0]

        exist_student = User.undeleted_objects.filter(phone = student_data['phone']).first()
        if exist_student:
            student_data['password'] = exist_student.password
        else:
            student_data['password']=make_password(password)
        
        print('student password', student_data['password'])

        serializer = User_serializer(data=student_data, context={'request': request})
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        save_student=serializer.save()

        #Save student preference
        if exist_student:   
            UserPreference.undeleted_objects.filter(user = exist_student.id).update(school=school_id)
        else:
            #Save user preference
            user_preference = {}
            user_preference['user'] = save_student.id
            user_preference['school'] = school_id
            serializer_preference = User_Preference_serializer(data = user_preference)
            
            if not serializer_preference.is_valid():
                User.undeleted_objects.filter(id = save_student.id).delete()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer_preference.save()

        # Save Card Model
        data_card = dossier_data
        data_card['student'] = save_student.id
        data_card['manual_price'] = False
        data_card['school'] = school_id
        serializer = Card_serializer(data=data_card)
        if not serializer.is_valid():
            print('error card serializer', serializer.errors)
            User.undeleted_objects.filter(id=save_student.id).delete()
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST,)
        save_card=serializer.save()

        # Save Card Status History
        history_data={
                    'card':save_card.id,
                    'status':1,
                    'date':datetime.now().date(),
                    'created_by':request.user.id
                    }
        serializer_history=Card_status_serializer(data=history_data)

        if not serializer_history.is_valid():
            Student.undeleted_objects.filter(id=serializer.data['id']).delete()
            Card.undeleted_objects.filter(id=save_card.data['id']).delete()
            return Response(serializer_history.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer_history.save()

        #Save nofications
        #get users
        student = save_card.student
        owner = User.undeleted_objects.filter(school=student.school.id, role=3).first()  # Get the owner of the school
        audiance = []
        audiance.append(student)
        if owner and owner != request.user:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Activity',
            'card',
            'Nouveau dossier créé 🗂️',
            f'Un nouveau dossier a été créé pour {save_card.student.first_name} {save_card.student.last_name}',
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)



@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def card_edit(request, id):
    try:
        card = Card.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Card_serializer_read(card)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        data=request.data.copy()
        if data['status'] != 99:
            data['end_at']=None
        data['school'] = card.school.id
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
        owner = User.undeleted_objects.filter(school=student.school.id, role=3).first()  # Get the owner of the school
        audiance = []
        audiance.append(student)
        if owner and owner != request.user:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Activity',
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
        owner = User.undeleted_objects.filter(school=student.school.id, role=3).first()  # Get the owner of the school
        audiance = []
        audiance.append(student)
        if owner and owner != request.user:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Activity',
            'card',
            'Dossier supprimé 🚮',
            f'Le dossier numéro {card.id} de {card.student.first_name} {card.student.last_name} a été supprimé',
        )

        return Response(status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def card_history(request, card_id):
        history=CardStatusHistory.undeleted_objects.filter(card=card_id).all()
        if not history:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer_history = Card_status_serializer_read(history,many=True)
        return Response(serializer_history.data, status=status.HTTP_200_OK)

# Acitivity CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
def session(request, school_id):
    if request.method == 'GET':
        sessions = Session.undeleted_objects.filter(school=school_id).all()
        if get_user_role(request.user.role) == 'Student':
            # If user is student, filter sessions by student id
            sessions = Session.undeleted_objects.filter(school=school_id, card__student__phone=request.user.phone).all()
        if not sessions:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Session_serializer_read(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':

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
        
        data = request.data.copy()
        data['school'] = school_id
        serializer = Session_serializer_edit(data=data)
        if not serializer.is_valid():
            print('error', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        save_session = serializer.save()

        #Save nofications
        #get users
        audiance = []

        try:
            student = save_session.card.student
            msg = f'Un nouveau session a été créé pour {student.first_name} {student.last_name}'
        except AttributeError:
            student = None
        
        if student:
            audiance.append(student)
        else:
            msg = 'Un nouveau session a été créé'

        trainer = save_session.employee

        if trainer and trainer != request.user:
            audiance.append(trainer)

        push_notification_to_users(
            audiance,
            'Activity',
            'card',
            'Nouveau session créé ⏰',
            msg,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def week_sessions(request, school_id):

    #Get Week start and end days
    # Date d'aujourd'hui
    today = date.today()
    week_days = today.weekday()
    week_first_day = today - timedelta(days=week_days)
    week_last_day = week_first_day + timedelta(days=6)
    sessions = Session.undeleted_objects.filter(employee__school=school_id).filter(day__gte=week_first_day, day__lte=week_last_day).all()
    if get_user_role(request.user.role) == 'Student':
        # If user is student, filter sessions by student id
        sessions = sessions.filter(card__student=request.user.id)
    if not sessions:
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = Session_serializer_read(sessions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def card_session(request, card_id):
    if request.method == 'GET':
        if not (sessions := Session.undeleted_objects.filter(card=card_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Session_serializer_read(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def session_edit(request, id):
    try:
        session = Session.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = Session_serializer_edit(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':

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

        data = request.data.copy()
        data['school'] = session.school.id
        serializer = Session_serializer_edit(session, data=data)

        if not serializer.is_valid():
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        save_session = serializer.save()
        #Save nofications
        #get users
        audiance = []

        try:
            student = save_session.card.student
            msg = f'Une session a été modifiée pour {student.first_name} {student.last_name}'
        except AttributeError:
            student = None
        
        if student:
            audiance.append(student)
        else:
            msg = 'Une session a été modifiée'

        trainer = save_session.employee

        if trainer and trainer != request.user:
            audiance.append(trainer)

        push_notification_to_users(
            audiance,
            'Activity',
            'card',
            'Session modifié ⏰',
            msg,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        session.delete()
        # session.is_deleted = True
        # session.deleted_at = datetime.now()
        # session.save()
        # serializer = Session_serializer_edit(session)
        #Save nofications
        #get users
        audiance = []
        try:
            student = session.card.student
        except AttributeError:
            student = None

        if student:
            audiance
            msg = f'Une session a été supprimée pour {student.first_name} {student.last_name}'
        else:
            msg = 'Une session a été supprimée'

        trainer = session.employee
        audiance.append(student)
        if trainer and trainer != request.user:
            audiance.append(trainer)

        push_notification_to_users(
            audiance,
            'Activity',
            'card',
            'Session supprimé 🚮',
            msg,
        )
        return Response(status=status.HTTP_201_CREATED)

# Employee CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def employee(request,school_id):
    user=request.user
    if request.method == 'GET':
        employees = User.undeleted_objects.filter(school=school_id, role__in = [3,4]).all() # 3 for owner, 4 for trainer
        if not employees:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = User_serializer_read(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'POST':
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
        
        #Check if already a employee is in the base
        exist_employee = User.undeleted_objects.filter(phone = employee_data['phone']).first()
        employee_data['username']=generete_username(employee_data['first_name'][0])
        if exist_employee:
            print('User already exist')
            employee_data['password'] = exist_employee.password
        else:
            password = generete_password()
            employee_data['password']=make_password(password)

        employee_data['role'] = 4 #trainer
        serializer = User_serializer(data=employee_data)
        if not serializer.is_valid():
            print('serializer error', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        obj = serializer.save()

        # #Save user preference
        #Update User School Preference is usera already exist
        if exist_employee:
            print('new preference school id', school_id)
            print('user id', exist_employee.id)
            # print('user', UserPreference.undeleted_objects.filter(user = obj.id).get())      
            UserPreference.undeleted_objects.filter(user = exist_employee.id).update(school=school_id)
        
        #Else create new Preference
        else:
            user_preference = {}
            user_preference['user'] = obj.id
            user_preference['school'] = school_id
            serializer_preference = User_Preference_serializer(data = user_preference)
            if not serializer_preference.is_valid():
                print('serializer_preference error', serializer_preference.errors)
                User.undeleted_objects.filter(id = obj.id).delete()
                return Response(serializer_preference.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer_preference.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def employee_edit(request, id):
    user=request.user
    try:
        employee = User.undeleted_objects.get(id=id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = User_serializer_read(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
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

        serializer = User_serializer(employee, data=employee_data)
        if not (serializer.is_valid()):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        employee.is_active = False
        employee.save()
        serializer = User_serializer(employee)
        return Response(status=status.HTTP_201_CREATED)


# Car CRUD
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def car(request,school_id):
    user=request.user
    print('school id', school_id)
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def car_edit(request, id):
    try:
        car = Car.undeleted_objects.get(id=id)
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

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        car.is_deleted = True
        car.deleted_at = datetime.now()
        car.save()
        serializer = Car_serializer(car)

        return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def licence(request):
    if request.method == 'GET':
        if not (licences := LicenceType.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Licence_serializer(licences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def status_status(request):
    if request.method == 'GET':
        if not (status_status_data := Status.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Status_serializer(status_status_data, many=True)
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
        data = request.data.copy()
        print('data', data)
        # #Format owner data
        owner_data['role'] = 3  # For owner
        owner_data['first_name'] = data['first_name']
        owner_data['last_name'] = data['last_name']
        owner_data['phone'] = data['phone']
        owner_data['governorate'] = data['governorate']
        owner_data['school'] = None
        owner_data['password'] =  make_password(data['password'])
        owner_data['username'] =  ''.join([data['first_name'], data['last_name']]).lower().replace(' ', '')
        owner_serializer = User_serializer_register(data=owner_data)

        # #Save Owner Model
        if not owner_serializer.is_valid():
            return Response(owner_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        owner_serializer.save()

        #Format school data
        school_data['name']=data['school_name']
        school_data['code']=data['school_code']
        school_serializer = School_serializer(data=school_data)
        #Save School Model
        if not school_serializer.is_valid():
            User.undeleted_objects.filter(id=owner_serializer.data['id']).delete()
            return Response(school_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        school_serializer.save()

        #Save Owner School Relation
        User.undeleted_objects.filter(id=owner_serializer.data['id']).update(school=school_serializer.data['id'])
        owner_serializer = User_serializer_read(User.undeleted_objects.get(id=owner_serializer.data['id']))
    
        #Save User preferences school relation
        preference = {}
        preference['user'] = owner_serializer.data['id']
        preference['school'] = school_serializer.data['id']
        preference_serializer = User_Preference_serializer(data=preference)

        if not preference_serializer.is_valid():
            User.undeleted_objects.filter(id=owner_serializer.data['id']).delete()
            School.undeleted_objects.filter(id=school_serializer.data['id']).delete()
            return Response(preference_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        preference_serializer.save()
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
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
def notification(request):
    if request.method == 'GET':
        # notifications = Notification.undeleted_objects.filter(user=request.user).all()
        notifications = Notification.undeleted_objects.all()
        if get_user_role(request.user.role) == 'Student':
            # If user is student, filter notifications by student id
            notifications = notifications.filter(user=request.user.id)

        if not notifications:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer=Notification_serializer_read(notifications,many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

# Employee CRUD
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
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
        owner = User.undeleted_objects.filter(school=student.school.id, role=3).first()  # Get the owner of the school
        audiance = []
        audiance.append(student)
        if owner and owner != request.user:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Activity',
            'payment',
            'Nouveau Payment 💰',
            f'Un payement de {save_payement.amount} a été effectué pour la carte {save_payement.card.id}.'
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET','PUT','DELETE'])
@permission_classes([IsAuthenticated, IsPaymentDone])
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
        owner = User.undeleted_objects.filter(school=student.school.id, role=3).first()  # Get the owner of the school
        audiance = []
        audiance.append(student)
        if owner and owner != request.user:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Activity',
            'payment',
            'Payment modifié 💰',
            f'le payement de {save_payement.amount} a été modifié pour la carte {save_payement.card.id}.'
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        payment.delete()
        #Save nofications
        # Prepare notification data
        # save_payement = (Payment.undeleted_objects
        #                 .select_related(
        #                     "card__student__user",
        #                 )
        #                 .get(pk=id))
        student = payment.card.student
        owner = User.undeleted_objects.filter(school=payment.card.school.id, role=3).first()
        audiance = []
        audiance.append(student)
        if owner and owner != request.user:
            audiance.append(owner)

        push_notification_to_users(
            audiance,
            'Activity',
            'payment',
            'Payment supprimé 🚮',
            f'le payement de {payment.amount} a été supprimé pour la carte {payment.card.id}.'
        )
        return Response(status=status.HTTP_201_CREATED)


# Payment CRUD
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def payment_dossier(request,card_id):
    if request.method == 'GET':
        if not (payments := Payment.undeleted_objects.filter(card=card_id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Payments_serializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
# @permission_classes([IsAuthenticated, IsPaymentDone])
def countries(request):
    if request.method == 'GET':
        if not (countries := Country.undeleted_objects.all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Country_serializer(countries, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
# @permission_classes([IsAuthenticated, IsPaymentDone])
def governorates(request, id):
    if request.method == 'GET':
        if not (governorates := Governorate.undeleted_objects.filter(country=id).all()):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = Governorate_serializer(governorates, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
# @permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
def profile(request):
    user_id=request.user.id

    try:
        profile = User.undeleted_objects.get(id=user_id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':

        profile_serialzer= User_serializer_read(profile)
        
        return Response(profile_serialzer.data, status=status.HTTP_200_OK)
    
    if request.method == 'PUT':
        # data=request.data.copy()
        profile_data = dict(request.data)
        # profile_data = {}
        # for key, value in data.items():
        #     if key.startswith('parts_'):
        #         profile_key = key.replace('parts_', '')
        #         profile_data[profile_key] = value
        print('profile_data', profile_data)
        if 'avatar' in request.FILES:
            profile_data['avatar'] = request.FILES['avatar']
        for key in profile_data:
            if isinstance(profile_data[key], list) and len(profile_data[key]) == 1:
                profile_data[key] = profile_data[key][0]

        profile_data['updated_by']=user_id
        profile_data['username']=profile.username
        profile_data['school']=profile.school.id
        profile_data['is_active']=profile.is_active
        profile_data['phone']=profile.phone
        dt = datetime.strptime(profile_data['birthday'], "%Y-%m-%dT%H:%M:%S.%fZ")
        profile_data['birthday'] = dt.strftime("%Y-%m-%d")
        print('data', profile_data)

        serializer=User_serializer(profile, data=profile_data, context={'request': request})

        if not (serializer.is_valid()):
            print('error profile', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsPaymentDone])
def change_password(request):
    if request.method == 'PUT':
        data = request.data.copy()
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        user = User.objects.get(id=request.user.id)
        if not user.check_password(old_password):
            return Response({"detail": "Ancien mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Mot de passe modifié avec succès."}, status=status.HTTP_200_OK)

#Notification PUSH
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])
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
@permission_classes([IsAuthenticated, IsPaymentDone])  # adapte si besoin
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
@permission_classes([IsAuthenticated, IsPaymentDone])
def notification_send(request):
    ser = NotificationSendSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    notif_id = ser.validated_data["notification_id"]

    # Vérifie que la notif existe (et appartient bien à quelqu'un)
    get_object_or_404(Notification, pk=notif_id)

    stats = send_pending_deliveries_for_notification(notif_id)
    return Response({"notification_id": notif_id, "stats": stats}, status=status.HTTP_200_OK)