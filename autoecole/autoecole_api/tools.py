import random
import string
from django.utils import timezone
from .models import Employee, Student, SchoolPayment


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



def user_has_valid_payment(user) -> bool:
    """
    Retourne True si l'utilisateur (via son école) a un paiement en cours de validité.
    """
    role = get_user_role(getattr(user, "fonction", None))

    # Récupère l'objet Employee/Student pour atteindre l'école
    owner_or_trainer = role in ["Owner", "Trainer"]
    if owner_or_trainer:
        holder = Employee.objects.filter(id=user.id).select_related("school").first()
    elif role == "Student":
        holder = Student.objects.filter(id=user.id).select_related("school").first()
    else:
        holder = None

    school = getattr(holder, "school", None)
    if not school:
        return False

    payment = (
        SchoolPayment.undeleted_objects
        .filter(school=school)
        .order_by("-date")
        .first()
    )
    if not payment or not payment.valid_until:
        return False

    # Utiliser la date locale (timezone-safe)
    today = timezone.localdate()
    return payment.valid_until >= today
