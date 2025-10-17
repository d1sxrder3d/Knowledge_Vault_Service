from django.urls import path
from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    
    # Auth
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Features
    path("tasks/add/", views.add_task_view, name="add_task"),
    path("documents/upload/", views.upload_document_view, name="upload_document"),
]