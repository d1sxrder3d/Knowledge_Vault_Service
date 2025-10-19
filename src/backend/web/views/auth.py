from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from web.forms.auth_forms import CustomUserCreationForm, CustomLoginForm


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


@login_required
def logout_view(request):
    logout(request)
    return redirect("index")
