from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


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
        from django.contrib.auth import get_user_model
        User = get_user_model()

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
