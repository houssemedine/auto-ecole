from django.contrib import admin
from autoecole_api.models import User,Owner, School, Student, Card, Activity, Session, Employee, Car, LicenceType,SessionType,Status
# Register your models here.
admin.site.register(User)
admin.site.register(Owner)
admin.site.register(School)
admin.site.register(Student)
admin.site.register(Card)
admin.site.register(Activity)
admin.site.register(Session)
admin.site.register(Employee)
admin.site.register(Car)
admin.site.register(LicenceType)
admin.site.register(SessionType)
admin.site.register(Status)
