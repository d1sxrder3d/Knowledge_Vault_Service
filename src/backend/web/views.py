from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django import forms
from django.contrib import messages
from django.forms.models import model_to_dict
from .forms import TaskForm, DocumentUploadForm

User = get_user_model()


# -------------------- РЕГИСТРАЦИЯ --------------------
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

# -------------------- ВХОД --------------------
class CustomLoginForm(forms.Form):
    login = forms.CharField(label="Имя пользователя или email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        login_input = cleaned_data.get("login")
        password = cleaned_data.get("password")

        user = None
        if login_input and password:
            # Пытаемся найти по username
            try:
                user = User.objects.get(username=login_input)
            except User.DoesNotExist:
                # Если нет — пробуем по email
                try:
                    user = User.objects.get(email=login_input)
                except User.DoesNotExist:
                    raise forms.ValidationError("Пользователь не найден")

            if not user.check_password(password):
                raise forms.ValidationError("Неверный логин или пароль")

        cleaned_data["user"] = user
        return cleaned_data


def index_view(request):
    just_logged_in = request.session.pop("just_logged_in", False)

    context = {
        "just_logged_in": just_logged_in,
        "tasks": [],
        "documents": [],
    }

    if request.user.is_authenticated:
        context["tasks"] = request.user.tasks.all().order_by("end_time")
        context["documents"] = request.user.documents.all().order_by("name")
    return render(request, "index.html", context)


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
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save()
            request.user.tasks.add(task)
            
            # Подготавливаем данные для ответа
            task_data = model_to_dict(task, fields=['id', 'name', 'description', 'end_time'])
            task_data['tags'] = [{'name': tag.name} for tag in task.tags.all()]
            
            return JsonResponse({'success': True, 'task': task_data})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    # Если это не AJAX POST, перенаправляем на главную
    return redirect('index')


@login_required
def upload_document_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        uploaded_files = request.FILES.getlist('files')
        if not uploaded_files:
            return JsonResponse({'success': False, 'error': 'Файлы не найдены.'})

        created_documents = []
        for uploaded_file in uploaded_files:
            # Упрощенная логика: имя документа = имя файла
            doc_split = uploaded_file.name.rsplit('.', 1)
            
            doc_name = doc_split[0]
            doc_ext = doc_split[1]
            
            form_data = {'name': doc_name, 'description': '', 'extension': doc_ext, 'project_id': ''}
            file_data = {'file': uploaded_file}
            
            form = DocumentUploadForm(form_data, file_data)

            if form.is_valid():
                document = form.save(commit=False)
                
                # Здесь должна быть логика сохранения файла (например, в S3 или локально)
                # Для примера, просто заполним поля метаданными
                document.file_name = uploaded_file.name
                document.file_weight = uploaded_file.size
                document.s3_path = f"user_{request.user.id}/{uploaded_file.name}" # Пример пути
                document.save()
                request.user.documents.add(document)

                doc_data = model_to_dict(document, fields=['id', 'name'])
                doc_data['extension'] = document.extension
                doc_data['uploaded_at_formatted'] = document.uploaded_at.strftime('%d.%m.%Y')
                created_documents.append(doc_data)
            else:
                # Можно добавить более детальную обработку ошибок
                print(f"Ошибка валидации для файла {uploaded_file.name}: {form.errors.as_json()}")

        if created_documents:
            return JsonResponse({'success': True, 'documents': created_documents})
        else:
            return JsonResponse({'success': False, 'error': 'Не удалось сохранить ни один из файлов.'})

    return redirect('index')
