from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.contrib.auth.views import LoginView


def home(request):
    if request.user.is_authenticated:
        user = request.user
        if User.user_type == "Teacher":
            context = {
                'message': "Bienvenido, Profesor.",
                'user_type': "Teacher"
            }
        elif User.user_type == "Student":
            context = {
                'message': "Bienvenido, Estudiante.",
                'user_type': "Student"
            }
        else:
            context = {
                'message': "Bienvenido.",
                'user_type': "Other"
            }
    else:
        context = {
            'message': "Bienvenido a la plataforma.",
            'user_type': "Guest"
        }

    return render(request, 'home.html', context)



def register(request):
    return render(request, 'register.html')


def register_student(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = User.UserTypeChoices.STUDENT
            user.save()
            return redirect('home')  # Redirige al login tras el registro exitoso
    else:
        form = UserCreationForm()
    return render(request, 'register_student.html', {'form': form, 'user_type': 'Estudiante'})

def register_teacher(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = User.UserTypeChoices.TEACHER
            user.save()
            return redirect('home')  # Redirige al login tras el registro exitoso
    else:
        form = UserCreationForm()
    return render(request, 'register_teacher.html', {'form': form, 'user_type': 'Profesor'})

class CustomLoginView(LoginView):
    template_name = 'login.html'