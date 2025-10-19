import json
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.forms.models import model_to_dict
from api.models import Task, Tag
from web.forms.task_forms import TaskForm
from web.views.utils import ajax_required, json_error, serialize_task, logger


@login_required
@ajax_required
@require_http_methods(["POST"])
def add_task_view(request):
    form = TaskForm(request.POST, user=request.user)
    if not form.is_valid():
        return json_error("Ошибка валидации", errors=form.errors)

    task = form.save(commit=False)
    task.user = request.user
    task.save()

    logger.info(f"Task created: {task.id} for user {request.user.id}")
    return JsonResponse({"success": True, "task": serialize_task(task)})


@login_required
@require_http_methods(["PATCH", "DELETE", "GET"])
def task_detail_view(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        return json_error("Задача не найдена", status=404)

    if request.method == "GET":
        return JsonResponse({"success": True, "task": serialize_task(task)})

    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return json_error("Неверный формат JSON")

        for field in ("name", "description", "status"):
            if field in data:
                setattr(task, field, data[field])

        if "end_time" in data:
            from django.utils.dateparse import parse_datetime
            task.end_time = parse_datetime(data["end_time"])

        task.save()

        if "tags" in data:
            task.tags.set(data["tags"])

        logger.info(f"Task updated: {task.id}")
        return JsonResponse({"success": True, "task": serialize_task(task)})

    if request.method == "DELETE":
        task.delete()
        logger.info(f"Task deleted: {task_id}")
        return JsonResponse({"success": True, "message": "Задача удалена"})
