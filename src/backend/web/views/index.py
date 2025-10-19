from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from api.models import Task, Document, Tag


@login_required
def index_view(request):
    tasks = (
        Task.objects.filter(user=request.user, parent__isnull=True)
        .prefetch_related("tags", "subtasks", "subtasks__tags")
        .order_by("-start_time")
    )
    documents = Document.objects.filter(user=request.user).order_by("-uploaded_at")
    tags = Tag.objects.filter(user=request.user).order_by("name")

    context = {
        "tasks": tasks,
        "documents": documents,
        "tags": tags,
        "just_logged_in": request.session.pop("just_logged_in", False),
    }
    return render(request, "index.html", context)
