from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from django.contrib.auth.views import LoginView


def home(request):
    if request.user.is_authenticated:
        user = request.user
        if user.user_type == "Teacher":
            context = {
                'message': "Bienvenido, Profesor.",
                'user_type': "Teacher"
            }
        elif user.user_type == "Student":
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
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'Student'
            user.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'Teacher'
            user.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register_teacher.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'login.html'


@login_required
def user_profile(request):
    user = request.user

    # Determina el tipo de usuario para mostrar información específica
    if user.is_teacher:
        user_type = "Profesor"
    elif user.is_student:
        user_type = "Estudiante"
    else:
        user_type = "Otro"

    context = {
        'user': user,
        'user_type': user_type,
    }

    return render(request, 'profile.html', context)