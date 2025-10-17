from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    class Meta:
        swappable = "AUTH_USER_MODEL"

    tags = models.ManyToManyField("Tag") # у юзера есть свой набор тэгов

    tasks = models.ManyToManyField("Task")
    
    documents = models.ManyToManyField("Document")

    projects = models.ManyToManyField("Project")


class Document(models.Model):
    class Meta:
        db_table = "documents"

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True, null=True)

    file_name = models.CharField(max_length=255)

    extension = models.CharField(max_length=255, blank=True, null=True)


    s3_path = models.CharField(max_length=255)
    
    file_weight = models.IntegerField()

    project = models.ForeignKey("Project", on_delete=models.CASCADE, blank=True, null=True)

    tags = models.ManyToManyField("Tag") # документу присваеваетя тэг
    
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Task(models.Model):
    class Meta:
        db_table = "tasks"

    name = models.CharField(max_length=255)

    description = models.TextField()

    status = models.CharField(max_length=255)

    project = models.ForeignKey("Project", on_delete=models.CASCADE, blank=True, null=True)

    end_time = models.DateTimeField(blank=True, null=True)

    start_time = models.DateTimeField(blank=True, null=True)

    parent = models.ForeignKey(
        'self',                    
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'    
    )

    tags = models.ManyToManyField("Tag",blank=True)



class Tag(models.Model):
    class Meta:
        db_table = "tags"

    name = models.CharField(max_length=50, unique=True)
    
    description = models.TextField(blank=True, null=True)

    color = models.CharField(max_length=40)

class Project(models.Model):
    class Meta:
        db_table = "projects"

    ACCESS_PUBLIC = "public"
    ACCESS_PRIVATE = "private"
    ACCESS_PROTECTED = "protected"

    ACCESS_MODIFIER_CHOICES = (
        (ACCESS_PUBLIC, "Public"),
        (ACCESS_PRIVATE, "Private"),
        (ACCESS_PROTECTED, "Protected"),
    )

    name = models.CharField(max_length=255)

    #public - доступ любому пользователю
    #private - только с инвайтом в проект
    #protected - по ссылке
    access_modifiers = models.CharField(
        max_length=10, choices=ACCESS_MODIFIER_CHOICES, default=ACCESS_PRIVATE
    )
    
    project_tags = models.ManyToManyField("Tag") 

    description = models.TextField(blank=True, null=True)

    icon = models.CharField(max_length=255)

    


#TODO: Рабочие пространства, членство и роли.

#TODO: Проекты и улучшение статусов