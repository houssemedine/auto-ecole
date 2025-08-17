from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework.decorators import permission_classes

User = get_user_model()

class TelBackend(ModelBackend):
    def authenticate(self, request, tel=None, password=None, **kwargs):
        print(f"Authenticating user with tel: {tel} and password: {password}")
        try:
            user = User.objects.get(tel=tel)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
