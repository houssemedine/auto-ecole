from rest_framework import permissions
from autoecole_api.models import Employee, SchoolPayment, Student
from .tools import get_user_role, user_has_valid_payment
from datetime import datetime


class IsManager(permissions.BasePermission):

    edit_methods = ("PUT", "PATCH")

    def has_permission(self, request, view):
        #Get User Role
        if user_role:=Employee.objects.filter(id=request.user.id).values():
            if (request.user.is_authenticated) and (user_role[0]['role'] == 'Manager'):
                return True

    def has_object_permission(self, request, view, obj):
        # if request.user.is_superuser:
        #     return True

        # if request.method in permissions.SAFE_METHODS:
        #     return True

        if request.user.role == 'Manager':
            return True

        # if request.user.is_staff and request.method not in self.edit_methods:
        #     return True

        return False
    

class IsPaymentDone(permissions.BasePermission):
    """
    Autorise uniquement si l'utilisateur a un paiement valide.
    """
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return user_has_valid_payment(user)