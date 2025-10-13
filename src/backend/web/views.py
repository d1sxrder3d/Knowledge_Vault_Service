from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages

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

