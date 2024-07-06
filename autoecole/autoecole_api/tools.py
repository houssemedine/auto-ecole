# Create your views here.
def generete_username(first_name, last_name, username_list):
    # Compose le nom complet initial
    # username = f"{first_name}{last_name}"
    username = f"{first_name[0].replace(' ','').lower()}{last_name.replace(' ','').lower()}"

    # Si le nom complet n'existe pas dans la liste, retournez-le directement
    if username not in username_list:
        return username

    # Sinon, ajoutez un suffixe numérique pour garantir l'unicité
    suffixe = 1
    username = f"{username}{suffixe}"
    while username in username_list:
        suffixe += 1
        username = f"{username}{suffixe}"

    return username