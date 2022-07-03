from datetime import datetime
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
    adress=models.TextField(max_length=100)
    city=models.CharField(max_length=150)
    governorate=models.CharField(max_length=50)
    country=models.CharField(max_length=50)
    speciality=models.CharField(max_length=50)
    mail=models.EmailField(blank=True,null=True)
    tel=models.IntegerField(blank=True,null=True)
    logo=models.ImageField(blank=True,null=True)

    def __str__(self) :
        return self.name