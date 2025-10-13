from django.db import models
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):

    class Meta:
        swappable = "AUTH_USER_MODEL"

    documents = models.ManyToManyField("Document")

    tags = models.ManyToManyField("tag") # у юзера есть свой набор тэгов

    tasks = models.ManyToManyField("task")

 

class Document(models.Model):
    class Meta:
        db_table = "documents"

    name = models.CharField(max_length=255)

    description = models.TextField()

    extension = models.CharField(max_length=10)

    tags = models.ManyToManyField("tag") # документу присваеваетя тэг


class Task(models.Model):
    class Meta:
        db_table = "tasks"

    name = models.CharField(max_length=255)

    description = models.TextField()

    end_time = models.DateTimeField()

    start_time = models.DateTimeField()

    tags = models.ManyToManyField("tag",blank=True)



class Tag(models.Model):
    class Meta:
        db_table = "tags"

    name = models.CharField(max_length=255, unique=True)
    
    description = models.TextField()

    color = models.CharField(max_length=40)
