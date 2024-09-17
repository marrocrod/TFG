from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import User, Event, Forum, Comment
from django.core.exceptions import ValidationError

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'})
    )
    degree = forms.ChoiceField(
        choices=User.DegreeChoices.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    group = forms.ChoiceField(
        choices=User.GroupChoices.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'degree', 'group']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']  

class ChatForm(forms.Form):
    user_input = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,  
            'placeholder': 'Escribe tu mensaje aquí...',  
            'class': 'form-control'  
        }), 
        label=''
    )

class ExerciseGenerationForm(forms.Form):
    topic = forms.ChoiceField(
        choices=[('', 'Seleccione un tema'), (1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6')],
        widget=forms.Select(attrs={'class': 'form-control form-control-lg custom-input'})
    )
    difficulty = forms.ChoiceField(
        choices=[('', 'Seleccione la dificultad'), ('Easy', 'Fácil'), ('Medium', 'Media'), ('Hard', 'Difícil')],
        widget=forms.Select(attrs={'class': 'form-control form-control-lg custom-input'})
    )
    number_of_exercises = forms.ChoiceField(
        choices=[('', 'Seleccione el número de ejercicios')] + [(i, f'{i} ejercicios') for i in range(1, 11)],
        widget=forms.Select(attrs={'class': 'form-control form-control-lg custom-input'})
    )
    set_name = forms.CharField(
        max_length=100,
        required=True,
        label="Nombre del Conjunto de Ejercicios",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg custom-input', 'placeholder': 'Introduce un nombre para el conjunto de ejercicios'})
    )



class ExamGenerationForm(forms.Form):
    exam_name = forms.CharField(
        max_length=100, 
        required=True, 
        label="Nombre del Examen",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm custom-input', 
            'placeholder': 'Introduce un nombre para el examen'
        })
    )
    topic_1 = forms.ChoiceField(
        choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6')],
        label="Tema del Ejercicio 1",
        widget=forms.Select(attrs={'class': 'form-control form-control-sm custom-input'})
    )
    topic_2 = forms.ChoiceField(
        choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6')],
        label="Tema del Ejercicio 2",
        widget=forms.Select(attrs={'class': 'form-control form-control-sm custom-input'})
    )
    topic_3 = forms.ChoiceField(
        choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6')],
        label="Tema del Ejercicio 3",
        widget=forms.Select(attrs={'class': 'form-control form-control-sm custom-input'})
    )
    topic_4 = forms.ChoiceField(
        choices=[(1, 'Tema 1'), (2, 'Tema 2'), (3, 'Tema 3'), (4, 'Tema 4'), (5, 'Tema 5'), (6, 'Tema 6')],
        label="Tema del Ejercicio 4",
        widget=forms.Select(attrs={'class': 'form-control form-control-sm custom-input'})
    )

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
