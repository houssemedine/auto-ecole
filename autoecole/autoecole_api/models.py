import datetime
from django.db import models

#BasedModel
class BaseModel(models.Model) :
    #created_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by= models.CharField(max_length= 30, default='Ibiza')
    updated_by = models.CharField(max_length= 30,default='Ibiza')
    
    class Meta :
        abstract = True 


#SoftDeleteManager
#creating a custom model manager to apply the filter 
#automatically without using filter(is_delete=False) 
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

#SoftDeleteModel
class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(null= False, default=False)
    deleted_by= models.CharField(max_length= 30,null=True,blank=True)
    deleted_at = models.DateTimeField(null=True,blank=True) 
    restored_at = models.DateTimeField(null=True,blank=True)
    restored_by = models.CharField(max_length= 30,null=True,blank=True)
    
    objects = models.Manager()
    undeleted_objects = SoftDeleteManager()

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()
    

    class Meta :
        #Django will not create a database table for this model
        abstract= True
# School model
class School(BaseModel,SoftDeleteModel):
    name=models.CharField(max_length=100)
    adress=models.TextField(max_length=150)
    city=models.CharField(max_length=50)
    governorate=models.CharField(max_length=50)
    country=models.CharField(max_length=50)
    speciality=models.CharField(max_length=50)
    email=models.EmailField(blank=True,null=True)
    tel=models.IntegerField(blank=True,null=True)
    logo=models.ImageField(blank=True,null=True)


    class Meta:
        ordering = ['name']
    def __str__(self) :
        return self.name

class Student(BaseModel,SoftDeleteModel):
    name=models.CharField(max_length=100)
    city=models.CharField(max_length=50)
    governorate=models.CharField(max_length=50)
    country=models.CharField(max_length=50)
    tel=models.IntegerField(blank=True,null=True)
    birthday=models.DateField()
    schools=models.ManyToManyField(School)


    class Meta:
        ordering = ['name']

    def __str__(self) :
        return self.name

class Card(BaseModel,SoftDeleteModel):
    licence_type=models.CharField(max_length=50)
    start_at=models.DateField()
    end_at=models.DateField()
    result=models.CharField(max_length=50,default='In progress')
    price=models.DecimalField( max_digits = 5, decimal_places = 2)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        ordering = ['licence_type']

    def __str__(self) :
        return self.licence_type

class Activity(BaseModel,SoftDeleteModel):
    name=models.CharField(max_length=50,unique=True)
    duration=models.FloatField(null=True,blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self) :
        return self.name


class Session(BaseModel,SoftDeleteModel):
    day=models.DateField()
    start_at=models.TimeField()
    end_at=models.TimeField()
    activity=models.ForeignKey(Activity,on_delete=models.CASCADE,null=True,blank=True)
    price=models.DecimalField(max_digits = 5, decimal_places = 2,null=True,blank=True)

    class Meta:
        ordering = ['day']

    def __str__(self) :
        return self.day.strftime("%d %b, %Y")

    #Session duration calcul
    @property
    def duration(self):
        date = datetime.date(1, 1, 1)
        datetime1 = datetime.datetime.combine(date, self.end_at)
        datetime2 = datetime.datetime.combine(date, self.start_at)
        return (datetime1 - datetime2)/3600







