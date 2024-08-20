from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Teacher, Student

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'degree', 'phone', 'password1', 'password2']

class TeacherRegistrationForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = []

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = []
