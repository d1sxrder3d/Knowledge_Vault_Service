from django.urls import path
from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    
    # Auth
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Tasks
    path("tasks/add/", views.add_task_view, name="add_task"),
    path("tasks/<int:task_id>/", views.task_detail_view, name="task_detail"),
    path("tasks/<int:task_id>/get/", views.task_get_view, name="task_get"),
    
    # Documents
    path("documents/upload/", views.upload_document_view, name="upload_document"),
    path("documents/<int:doc_id>/", views.document_detail_view, name="document_detail"),
    path("documents/<int:doc_id>/get/", views.document_get_view, name="document_get"),
]