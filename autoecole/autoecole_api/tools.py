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


def get_user_school(user):

    #get user fonction
    user_fonction=User.undeleted_objects.filter(user.id)
