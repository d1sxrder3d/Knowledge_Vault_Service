from django import forms
from api.models import Task, Document, Tag


class TaskForm(forms.ModelForm):
    """Форма для создания и редактирования задачи."""
    
    # Используем виджет для удобного выбора даты и времени
    end_time = forms.DateTimeField(
        label="Срок выполнения",
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    
    # Позволяем выбирать теги из выпадающего списка с возможностью множественного выбора
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(), # Заполним в __init__
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Теги"
    )

    class Meta:
        model = Task
        fields = ['name', 'description', 'end_time', 'tags']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Название задачи'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Подробное описание...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['tags'].queryset = user.user_tags.all()


class DocumentUploadForm(forms.ModelForm):
    """Форма для загрузки нового документа."""
    
    # Добавляем поле для загрузки файла, которого нет в модели
    file = forms.FileField(label="Файл")

    class Meta:
        model = Document
        fields = ['name', 'description', 'extension', 'project']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Название документа'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Краткое описание документа...'}),
        }