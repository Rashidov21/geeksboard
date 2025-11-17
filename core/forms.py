from django import forms

from .models import PointCategory, StudentPoint


class StudentPointForm(forms.ModelForm):
    class Meta:
        model = StudentPoint
        fields = ['category', 'score', 'note']
        widgets = {
            'note': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = PointCategory.objects.filter(is_active=True)
        self.fields['score'].widget.attrs.update({'min': 0, 'max': 10, 'type': 'number'})


