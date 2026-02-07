from django import forms
from .models import Vocabulary, StudySession


class VocabularyInputForm(forms.Form):
    """Form nhập từ vựng - chỉ cần nhập 1 trong 2: tiếng Trung hoặc tiếng Việt"""

    chinese = forms.CharField(
        max_length=100,
        required=False,
        label="Tiếng Trung",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Nhập từ tiếng Trung (ví dụ: 你好)",
            }
        ),
    )
    vietnamese = forms.CharField(
        max_length=200,
        required=False,
        label="Tiếng Việt",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Nhập từ tiếng Việt (ví dụ: xin chào)",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        chinese = cleaned_data.get("chinese")
        vietnamese = cleaned_data.get("vietnamese")

        if not chinese and not vietnamese:
            raise forms.ValidationError(
                "Vui lòng nhập ít nhất tiếng Trung hoặc tiếng Việt!"
            )

        return cleaned_data


class StudySessionForm(forms.ModelForm):
    """Form tạo buổi học mới"""

    class Meta:
        model = StudySession
        fields = ["date", "duration_minutes", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "duration_minutes": forms.NumberInput(
                attrs={"class": "form-input", "min": "1"}
            ),
            "notes": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }
