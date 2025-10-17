from rest_framework import serializers
from .models import *


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):


    start_time = serializers.DateTimeField(required=True)
    end_time = serializers.DateTimeField(required=True)

    class Meta:
        model = Task
        fields = '__all__'

    def validate(self, data):
        """
        Проверка что время окончания задачи больше времени начала
        """
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("Время окончания должно быть больше времени начала")
        return data
    

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class ProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
    
    def validate(self, data):

        if data['name'] in Project.objects.all().values_list('name', flat=True):
            raise serializers.ValidationError("Проект с таким названием уже существует")
        return data