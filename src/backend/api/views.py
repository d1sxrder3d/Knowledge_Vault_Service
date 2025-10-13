from rest_framework import viewsets
from .models import Task, Tag
from .serializers import TaskSerializer, TagSerializer


class TaskViewSet(viewsets.ModelViewSet):
    
    queryset = Task.objects.all().order_by('-start_time')
    serializer_class = TaskSerializer


class TagViewSet(viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
