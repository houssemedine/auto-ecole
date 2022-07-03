from django.urls import path
from autoecole_api import views
urlpatterns = [
    # School URL
        # index and save
    path('school/',views.school,name='school'),
        # edit and delete
    path('school/<int:id>/edit',views.school_edit,name='school_edit'),

    # Student URL
            # index and save
    path('student/',views.student,name='student'),
            # edit and delete
    path('student/<int:id>/edit',views.student_edit,name='student_edit'),

    # Card URL
            # index and save
    path('card/',views.card,name='card'),
            # edit and delete
    path('card/<int:id>/edit',views.card_edit,name='card_edit'),

    # Activity URL
            # index and save
    path('activity/',views.activity,name='activity'),
            # edit and delete
    path('activity/<int:id>/edit',views.activity_edit,name='activity_edit'),

]