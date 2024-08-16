from django.urls import path
from autoecole_api import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

# from autoecole_api.views import MyTokenObtainPairView




urlpatterns = [
        #JWT URL
                #Acces Token
        path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
                #Refresh Token
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),



        # School URL
                # index and save
        path('school/<int:id>',views.school,name='school'),
                # edit and delete
        path('school/<int:id>/edit',views.school_edit,name='school_edit'),

        # Student URL
                # index and save
        path('school/<int:school_id>/student/',views.student,name='student'),
                # edit and delete
        path('student/<int:id>/edit',views.student_edit,name='student_edit'),

        # Card URL
                # index and save
        path('cards/',views.card,name='card'),
                # edit and delete
        path('cards/<int:id>/edit',views.card_edit,name='card_edit'),

        # Activity URL
                # index and save
        path('activity/',views.activity,name='activity'),
                # edit and delete
        path('activity/<int:id>/edit',views.activity_edit,name='activity_edit'),


        # Session URL
                # index and save
        path('session/',views.session,name='session'),
                # edit and delete
        path('session/<int:id>/edit',views.session_edit,name='session_edit'),

        # Session URL
                # index and save
        path('employee/',views.employee,name='employee'),
                # edit and delete
        path('employee/<int:id>/edit',views.employee_edit,name='employee_edit'),

        # Car URL
                # index and save
        path('car/',views.car,name='car'),
                # edit and delete
        path('car/<int:id>/edit',views.car_edit,name='car_edit'),

        # Licence URL
                # index
        path('licences/',views.licence,name='licences'),

        # Licence URL
                # index
        path('owners/',views.owner,name='owners'),

        # Session Types URL
                # index
        path('sessiontypes/',views.session_types,name='sessiontypes'),

        # Register URL
                # index
        path('register/',views.register,name='register'),

]