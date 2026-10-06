from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Student


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'gender', 'location', 'age',
            'telephone', 'email', 'username',
            'passport_photo', 'academic_documents',
            'password1', 'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        qs = Student.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user