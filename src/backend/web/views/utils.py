import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from functools import wraps

logger = logging.getLogger(__name__)


def ajax_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "AJAX required"}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapped


def json_error(message, status=400, **extra):
    return JsonResponse({"success": False, "message": message, **extra}, status=status)


def serialize_tags(tags):
    return [{"id": t.id, "name": t.name, "color": getattr(t, "color", None)} for t in tags]


def serialize_task(task):
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "status": task.status,
        "end_time": task.end_time.strftime("%Y-%m-%d %H:%M") if task.end_time else None,
        "tags": serialize_tags(task.tags.all())
    }


def serialize_document(doc):
    return {
        "id": doc.id,
        "name": doc.name,
        "description": doc.description,
        "extension": doc.extension,
        "uploaded_at": doc.uploaded_at.strftime("%Y-%m-%d"),
        "tags": serialize_tags(doc.tags.all())
    }
