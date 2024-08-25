from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Exercise

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']  # Añade otros campos según sea necesario

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'degree']  # Añade otros campos que quieras que el usuario pueda editar


class ChatForm(forms.Form):
    user_input = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='Escribe tu mensaje')


class ExerciseGenerationForm(forms.Form):
    topic = forms.ChoiceField(choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6'), (7, 'Tema 7')])
    difficulty = forms.ChoiceField(choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')])
    number_of_exercises = forms.ChoiceField(choices=[(1, '1 ejercicio'), (2, '2 ejercicios'), (3, '3 ejercicios'), (4, '4 ejercicios')])
    set_name = forms.CharField(max_length=100, required=True, label="Nombre del Conjunto de Ejercicios")  # Campo para el nombre


