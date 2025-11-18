from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Mentor, PointCategory, StudentPoint

User = get_user_model()


class MentorRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone = forms.CharField(max_length=32, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            mentor = Mentor.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
                address=self.cleaned_data.get('address', ''),
            )
        return user


class StudentPointForm(forms.ModelForm):
    class Meta:
        model = StudentPoint
        fields = ['category', 'score', 'reason', 'note']
        widgets = {
            'reason': forms.TextInput(attrs={'placeholder': 'Why points were given/removed'}),
            'note': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = PointCategory.objects.filter(is_active=True)
        self.fields['score'].widget.attrs.update({'min': -10, 'max': 10, 'type': 'number', 'step': 1})
        self.fields['score'].help_text = 'Positive to add points, negative to remove points'


