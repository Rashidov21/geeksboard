from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Group, Mentor, PointCategory, Student, StudentPoint

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


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'subject', 'schedule', 'start_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'placeholder': 'Guruh nomi'}),
            'subject': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'placeholder': 'Fan nomi'}),
            'schedule': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'placeholder': 'Dars jadvali'}),
            'start_date': forms.DateInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'type': 'date'}),
        }
        labels = {
            'name': 'Guruh nomi',
            'subject': 'Fan',
            'schedule': 'Jadval',
            'start_date': 'Boshlanish sanasi',
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'birth_date', 'phone', 'parent_phone', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'placeholder': 'To\'liq ism'}),
            'birth_date': forms.DateInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'placeholder': 'Talaba telefoni'}),
            'parent_phone': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'placeholder': 'Ota-ona telefoni'}),
            'notes': forms.Textarea(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'rows': 3, 'placeholder': 'Qo\'shimcha eslatmalar'}),
        }
        labels = {
            'full_name': 'To\'liq ism',
            'birth_date': 'Tug\'ilgan sana',
            'phone': 'Talaba telefoni',
            'parent_phone': 'Ota-ona telefoni',
            'notes': 'Eslatmalar',
        }


class StudentPointForm(forms.ModelForm):
    class Meta:
        model = StudentPoint
        fields = ['category', 'score', 'reason', 'note']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30'}),
            'score': forms.NumberInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30', 'min': -10, 'max': 10, 'step': 1}),
            'reason': forms.TextInput(attrs={'placeholder': 'Ball berilgan/olib tashlangan sabab', 'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30'}),
            'note': forms.TextInput(attrs={'placeholder': 'Ixtiyoriy eslatma', 'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30'}),
        }
        labels = {
            'category': 'Kategoriya',
            'score': 'Ball',
            'reason': 'Sabab',
            'note': 'Eslatma',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = PointCategory.objects.filter(is_active=True)
        self.fields['score'].help_text = 'Musbat - qo\'shish, manfiy - olib tashlash'


