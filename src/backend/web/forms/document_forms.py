from django import forms
from api.models import Document, Tag



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