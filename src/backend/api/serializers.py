from rest_framework import serializers
from .models import Task, Tag


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