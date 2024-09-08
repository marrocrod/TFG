from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import User, Event, Forum, Comment
from django.core.exceptions import ValidationError

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    degree = forms.ChoiceField(choices=User.DegreeChoices.choices, required=True)
    group = forms.ChoiceField(choices=User.GroupChoices.choices, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'degree', 'group']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']  

class ChatForm(forms.Form):
    user_input = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='Escribe tu mensaje')


class ExerciseGenerationForm(forms.Form):
    topic = forms.ChoiceField(choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6'), (7, 'Tema 7')])
    difficulty = forms.ChoiceField(choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')])
    number_of_exercises = forms.ChoiceField(choices=[(1, '1 ejercicio'), (2, '2 ejercicios'), (3, '3 ejercicios'), (4, '4 ejercicios')])
    set_name = forms.CharField(max_length=100, required=True, label="Nombre del Conjunto de Ejercicios")  # Campo para el nombre


class ExamGenerationForm(forms.Form):
    exam_name = forms.CharField(max_length=100, required=True, label="Nombre del Examen")
    topic_1 = forms.ChoiceField(choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6'), (7, 'Tema 7')], label="Tema del Ejercicio 1")
    topic_2 = forms.ChoiceField(choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6'), (7, 'Tema 7')], label="Tema del Ejercicio 2")
    topic_3 = forms.ChoiceField(choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6'), (7, 'Tema 7')], label="Tema del Ejercicio 3")
    topic_4 = forms.ChoiceField(choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6'), (7, 'Tema 7')], label="Tema del Ejercicio 4")


class StudentSolutionForm(forms.Form):
    exercise_id = forms.IntegerField(widget=forms.HiddenInput())
    student_solution = forms.CharField(widget=forms.Textarea, required=False)

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'start_time', 'end_time', 'color']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            raise ValidationError("La hora de finalización debe ser posterior a la hora de inicio.")

        return cleaned_data


User = get_user_model()

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "Esta cuenta no está activada. Revisa tu correo para activar la cuenta.",
                code='inactive',
            )
        
class EmailUpdateForm(forms.Form):
    email = forms.EmailField(label='Nuevo Correo Electrónico')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return email
    

class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['title', 'description', 'image']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']