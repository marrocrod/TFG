from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Teacher, Student

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']  # Añade otros campos según sea necesario

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'degree']  # Añade otros campos que quieras que el usuario pueda editar
