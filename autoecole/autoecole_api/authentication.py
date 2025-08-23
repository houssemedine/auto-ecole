from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework.decorators import permission_classes
from .models import User
# User = get_user_model()

class TelBackend(ModelBackend):
    def authenticate(self, request, phone=None, password=None, **kwargs):
        # try:
        print('phone', phone)
        user = User.objects.get(phone=phone)
        print(user)
        # except User.DoesNotExist:
        #     return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
