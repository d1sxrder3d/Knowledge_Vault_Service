import json
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from api.models import Document
from web.forms.document_forms import DocumentUploadForm
from .utils import ajax_required, json_error, serialize_document, logger


@login_required
@ajax_required
@require_http_methods(["POST"])
def upload_document_view(request):
    uploaded_files = request.FILES.getlist("files")
    if not uploaded_files:
        return json_error("Файлы не найдены")

    created_docs = []

    for file in uploaded_files:
        name, _, ext = file.name.partition(".")
        form = DocumentUploadForm({
            "name": name,
            "description": "",
            "extension": ext,
        }, {"file": file})

        if not form.is_valid():
            continue

        document = form.save(commit=False)
        document.user = request.user
        document.file_name = file.name
        document.file_weight = file.size
        document.s3_path = f"user_{request.user.id}/{file.name}"
        document.save()

        created_docs.append(serialize_document(document))
        logger.info(f"Document uploaded: {document.id}")

    if not created_docs:
        return json_error("Не удалось сохранить файлы")

    return JsonResponse({"success": True, "documents": created_docs})


@login_required
@require_http_methods(["PATCH", "DELETE", "GET"])
def document_detail_view(request, doc_id):
    try:
        document = Document.objects.get(id=doc_id, user=request.user)
    except Document.DoesNotExist:
        return json_error("Документ не найден", status=404)

    if request.method == "GET":
        return JsonResponse({"success": True, "document": serialize_document(document)})

    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return json_error("Неверный формат JSON")

        for field in ("name", "description"):
            if field in data:
                setattr(document, field, data[field])

        document.save()

        if "tags" in data:
            document.tags.set(data["tags"])

        logger.info(f"Document updated: {document.id}")
        return JsonResponse({"success": True, "document": serialize_document(document)})

    if request.method == "DELETE":
        document.delete()
        logger.info(f"Document deleted: {doc_id}")
        return JsonResponse({"success": True, "message": "Документ удалён"})
