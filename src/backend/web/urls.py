from django.urls import path
from web.views import index, auth, tasks, documents

urlpatterns = [
    path("", index.index_view, name="index"),
    
    path("register/", auth.register_view, name="register"),
    path("login/", auth.login_view, name="login"),
    path("logout/", auth.logout_view, name="logout"),
    
    path("tasks/add/", tasks.add_task_view, name="add_task"),
    path("tasks/<int:task_id>/", tasks.task_detail_view, name="task_detail"),
    
    path("documents/upload/", documents.upload_document_view, name="upload_document"),
    path("documents/<int:doc_id>/", documents.document_detail_view, name="document_detail"),
]