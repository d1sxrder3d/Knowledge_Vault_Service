import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django import forms
from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json


from api.models import Task, Document, Tag
from .forms import TaskForm, DocumentUploadForm

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomLoginForm(forms.Form):
    login = forms.CharField(label="Имя пользователя или email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        login_input = cleaned_data.get("login")
        password = cleaned_data.get("password")

        user = None
        if login_input and password:
            try:
                user = User.objects.get(username=login_input)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=login_input)
                except User.DoesNotExist:
                    raise forms.ValidationError("Пользователь не найден")

            if not user.check_password(password):
                raise forms.ValidationError("Неверный логин или пароль")

        cleaned_data["user"] = user
        return cleaned_data


@login_required
def index_view(request):
    tasks = Task.objects.filter(
        user=request.user,
        parent__isnull=True
    ).prefetch_related('tags', 'subtasks', 'subtasks__tags').order_by('-start_time')
    
    documents = Document.objects.filter(user_id=request.user).order_by('-uploaded_at')
    tags = Tag.objects.filter(user=request.user).order_by('name')

    context = {
        'tasks': tasks,
        'documents': documents,
        'tags': tags,
        'just_logged_in': request.session.pop('just_logged_in', False)
    }
    
    return render(request, 'index.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Регистрация прошла успешно! Теперь войди.")
            return redirect("login")
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            request.session["just_logged_in"] = True
            return redirect("index")
    else:
        form = CustomLoginForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("index")


@login_required
def add_task_view(request):
    if request.method != 'POST' or request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return redirect('index')
    
    parent_id = request.POST.get('parent_id', '').strip()
    
    if parent_id:
        return _create_subtask(request, parent_id)
    
    return _create_task(request)


def _create_subtask(request, parent_id):
    try:
        parent_task = Task.objects.get(id=parent_id, user=request.user)
        name = request.POST.get('name', '').strip()
        
        if not name:
            return JsonResponse({
                'success': False,
                'errors': {'name': ['Название обязательно']},
                'message': 'Введите название подзадачи'
            })
        
        subtask = Task.objects.create(
            name=name,
            description='',
            user=request.user,
            parent=parent_task,
            end_time=parent_task.end_time
        )
        
        if parent_task.tags.exists():
            subtask.tags.set(parent_task.tags.all())
        
        task_data = {
            'id': subtask.id,
            'name': subtask.name,
            'description': subtask.description,
            'end_time': subtask.end_time.strftime('%Y-%m-%d %H:%M') if subtask.end_time else None,
            'tags': [{'id': tag.id, 'name': tag.name} for tag in subtask.tags.all()]
        }
        
        logger.info(f"Subtask created: {subtask.id} for user {request.user.id}")
        
        return JsonResponse({
            'success': True,
            'task': task_data,
            'message': f'Подзадача "{name}" добавлена'
        })
        
    except Task.DoesNotExist:
        return JsonResponse({
            'success': False,
            'errors': {'parent': ['Родительская задача не найдена']},
            'message': 'Ошибка при добавлении подзадачи'
        })
    except Exception as e:
        logger.error(f"Error creating subtask: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': [str(e)]},
            'message': 'Произошла ошибка'
        })


def _create_task(request):
    post_data = request.POST.copy()
    existing_tags_str = post_data.pop('existing_tags', [''])[0].strip()
    new_tags_str = post_data.pop('new_tags', [''])[0].strip()
    
    form = TaskForm(post_data, user=request.user)
    
    if not form.is_valid():
        errors = {field: [str(error) for error in error_list] 
                 for field, error_list in form.errors.items()}
        return JsonResponse({
            'success': False, 
            'errors': errors,
            'message': 'Пожалуйста, исправьте ошибки в форме'
        })
    
    task = form.save(commit=False)
    task.user = request.user
    task.save()
    
    task_tags = _process_tags(request.user, existing_tags_str, new_tags_str)
    if task_tags:
        task.tags.set(task_tags)
    
    task_data = model_to_dict(task, fields=['id', 'name', 'description', 'end_time'])
    task_data['tags'] = [{'id': tag.id, 'name': tag.name} for tag in task.tags.all()]
    
    if task.end_time:
        task_data['end_time'] = task.end_time.strftime('%Y-%m-%d %H:%M')
    
    logger.info(f"Task created: {task.id} for user {request.user.id}")
    
    return JsonResponse({
        'success': True, 
        'task': task_data,
        'message': f'Задача "{task.name}" успешно создана!'
    })


def _process_tags(user, existing_tags_str, new_tags_str):
    task_tags = []
    
    if existing_tags_str:
        try:
            existing_tag_ids = [int(id.strip()) for id in existing_tags_str.split(',') if id.strip()]
            existing_tags = Tag.objects.filter(id__in=existing_tag_ids, user=user)
            task_tags.extend(existing_tags)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error processing existing tags: {str(e)}")
    
    if new_tags_str:
        new_tag_names = [name.strip() for name in new_tags_str.split(',') if name.strip()]
        for tag_name in new_tag_names:
            if tag_name:
                tag, created = Tag.objects.get_or_create(
                    name__iexact=tag_name,
                    user=user,
                    defaults={'name': tag_name}
                )
                task_tags.append(tag)
    
    return task_tags


@login_required
def upload_document_view(request):
    if request.method != 'POST' or request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return redirect('index')
    
    uploaded_files = request.FILES.getlist('files')
    if not uploaded_files:
        return JsonResponse({'success': False, 'error': 'Файлы не найдены.'})

    created_documents = []
    
    for uploaded_file in uploaded_files:
        doc_split = uploaded_file.name.rsplit('.', 1)
        doc_name = doc_split[0]
        doc_ext = doc_split[1] if len(doc_split) > 1 else ''
        
        form_data = {
            'name': doc_name,
            'description': '',
            'extension': doc_ext,
            'project_id': ''
        }
        file_data = {'file': uploaded_file}
        
        form = DocumentUploadForm(form_data, file_data)

        if form.is_valid():
            document = form.save(commit=False)
            document.user_id = request.user
            document.file_name = uploaded_file.name
            document.file_weight = uploaded_file.size
            document.s3_path = f"user_{request.user.id}/{uploaded_file.name}"
            document.save()

            doc_data = model_to_dict(document, fields=['id', 'name'])
            doc_data['extension'] = document.extension
            doc_data['uploaded_at_formatted'] = document.uploaded_at.strftime('%d.%m.%Y')
            created_documents.append(doc_data)
            
            logger.info(f"Document uploaded: {document.id} for user {request.user.id}")
        else:
            logger.warning(f"Document validation error for {uploaded_file.name}: {form.errors.as_json()}")

    if created_documents:
        return JsonResponse({'success': True, 'documents': created_documents})
    
    return JsonResponse({'success': False, 'error': 'Не удалось сохранить ни один из файлов.'})


@login_required
@require_http_methods(["PATCH", "DELETE"])
def task_detail_view(request, task_id):
    """Обработка PATCH и DELETE запросов для задач"""
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Задача не найдена'}, status=404)
    
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            
            # Обновление статуса
            if 'status' in data:
                task.status = data['status']
                task.save()
                return JsonResponse({'success': True, 'status': task.status})
            
            # Обновление других полей
            if 'name' in data:
                task.name = data['name']
            if 'description' in data:
                task.description = data['description']
            if 'end_time' in data:
                from django.utils.dateparse import parse_datetime
                task.end_time = parse_datetime(data['end_time'])
            
            task.save()
            
            # Обновление тегов
            if 'tags' in data:
                task.tags.set(data['tags'])
            
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'status': task.status,
                    'end_time': task.end_time.strftime('%Y-%m-%d %H:%M') if task.end_time else None,
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    elif request.method == 'DELETE':
        try:
            task.delete()
            return JsonResponse({'success': True, 'message': 'Задача удалена'})
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def task_get_view(request, task_id):
    """Получение данных задачи"""
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'end_time': task.end_time.strftime('%Y-%m-%d %H:%M') if task.end_time else None,
                'tags': [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in task.tags.all()]
            }
        })
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Задача не найдена'}, status=404)


@login_required
@require_http_methods(["PATCH", "DELETE"])
def document_detail_view(request, doc_id):
    """Обработка PATCH и DELETE запросов для документов"""
    try:
        document = Document.objects.get(id=doc_id, user_id=request.user)
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Документ не найден'}, status=404)
    
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            
            if 'name' in data:
                document.name = data['name']
            if 'description' in data:
                document.description = data['description']
            
            document.save()
            
            # Обновление тегов
            if 'tags' in data:
                document.tags.set(data['tags'])
            
            return JsonResponse({
                'success': True,
                'document': {
                    'id': document.id,
                    'name': document.name,
                    'description': document.description,
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    elif request.method == 'DELETE':
        try:
            document.delete()
            return JsonResponse({'success': True, 'message': 'Документ удален'})
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def document_get_view(request, doc_id):
    """Получение данных документа"""
    try:
        document = Document.objects.get(id=doc_id, user_id=request.user)
        
        return JsonResponse({
            'success': True,
            'id': document.id,
            'name': document.name,
            'description': document.description,
            'extension': document.extension,
            'uploaded_at': document.uploaded_at.strftime('%Y-%m-%d'),
            'tags': [tag.id for tag in document.tags.all()]
        })
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Документ не найден'}, status=404)
