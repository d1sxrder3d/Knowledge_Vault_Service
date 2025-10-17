from rest_framework import viewsets, permissions
from .models import Task, Tag, Project, Document
from .serializers import *


class TaskViewSet(viewsets.ModelViewSet):

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.tasks.all().order_by('-start_time')
    


class TagViewSet(viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.tags.all()




class ProjectViewSet(viewsets.ModelViewSet):

    queryset = Project.objects.all()
    serializer_class = ProjectsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.project_set.all()


class DocumentViewSet(viewsets.ModelViewSet):

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.documents.all()
