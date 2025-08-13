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
        path('student/<int:id>/resetPassword',views.student_reset_password,name='student_reset_password'),
        path('student/<int:id>/enableDisableAccount',views.student_enable_disable_account,name='student_enable_disable_account'),

        # Card URL
                # index and save
        path('school/<int:school_id>/cards/<str:progress_status>/',views.card,name='card'),
        path('school/<int:school_id>/save_card_student/',views.save_card_and_student,name='card_and_student'),
                # edit and delete
        path('cards/<int:id>/edit',views.card_edit,name='card_edit'),

        # Activity URL
                # index and save
        path('activity/',views.activity,name='activity'),
                # edit and delete
        path('activity/<int:id>/edit',views.activity_edit,name='activity_edit'),


        # Session URL
                # index and save
        path('school/<int:school_id>/session/',views.session,name='session'),
        path('school/<int:school_id>/week_session/',views.week_sessions,name='session'),
                # edit and delete
        path('session/<int:id>/edit',views.session_edit,name='session_edit'),

        # Session URL
                # index and save
        path('school/<int:school_id>/employees/',views.employee,name='employee'),
                # edit and delete
        path('employee/<int:id>/edit',views.employee_edit,name='employee_edit'),

        # Car URL
                # index and save
        path('school/<int:school_id>/cars/',views.car,name='car'),
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

        # status URL
                # index
        path('status/',views.status_status,name='status'),

        # stats URL
                # index
        path('school/<int:school_id>/stats/',views.stats,name='stats'),

        # Payment URL
                # index and save
        path('school/<int:school_id>/payments/',views.payment,name='payment'),
        path('payment/<int:id>/edit',views.payment_edit,name='payment_edit'),


        #Payment for one card
        # index and save
        path('card/<int:card_id>/payments/',views.payment_dossier,name='card_payment'),

        #Card History
        path('card/<int:card_id>/history/',views.card_history,name='card_history'),

        #Session for one card
        path('card/<int:card_id>/sessions/',views.card_session,name='card_session'),

        #Notification
        path('notifications/',views.notification,name='notification'),
        path('notification/<int:id>/read',views.update_notification,name='update_notification'),
        path('notification/<int:id>/delete',views.delete_notification,name='delete_notification'),

        path("devices/register/", views.device_register, name="device-register"),
        path("devices/unregister/", views.device_unregister, name="device-unregister"),
        path("devices/ping/", views.device_ping, name="device-ping"),
        path("notifications/create/", views.notification_create, name="notification-create"),
        path("notifications/send/", views.notification_send, name="notification-send"),
        #Country
	path('countries/', views.countries, name='countries'),

        #Governorate
	path('countries/<int:id>/governorates/', views.governorates, name='governorates'),

        #Cities
	path('governorate/<int:id>/cities/', views.cities, name='cities'),

        #Profile
	path('profile/', views.profile, name='profile'),

]