import random
import string

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