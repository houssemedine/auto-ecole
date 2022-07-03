from django.urls import path
from autoecole_api import views
urlpatterns = [
    path('school/',views.school,name='school'),
    path('school/<int:id>/edit',views.school_edit,name='school_edit')
]