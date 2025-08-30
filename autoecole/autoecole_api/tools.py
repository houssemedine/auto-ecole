import random
import string
from django.utils import timezone
from .models import User, SchoolSubscription


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

def generete_username(first_name, last_name, username_list):
    username = f"{first_name[0].replace(' ','').lower()}{last_name.replace(' ','').lower()}"

    if username not in username_list:
        return username

    suffixe = 1
    username = f"{username}{suffixe}"
    while username in username_list:
        suffixe += 1
        username = f"{username}{suffixe}"

    return username


def generete_password():

    length = 6
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))

    return password

def generete_username(first_name):

    length = 6
    characters = string.ascii_letters + string.digits
    random_num = ''.join(random.choice(characters) for i in range(length))
    username = first_name + random_num
    return username



def user_has_valid_payment(user) -> bool:
    """
    Retourne True si l'utilisateur (via son école) a un paiement en cours de validité.
    """
    school = User.objects.get(id=user.id).school
    if not school:
        return False

    payment = (
        SchoolSubscription.undeleted_objects
        .filter(school=school)
        .order_by("-date")
        .first()
    )
    if not payment or not payment.valid_until:
        return False

    # Utiliser la date locale (timezone-safe)
    today = timezone.localdate()
    return payment.valid_until >= today
