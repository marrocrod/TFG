from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm, TeacherRegistrationForm, StudentRegistrationForm

def home (request):
    return render(request, 'home.html')

def register_view(request):
    return render(request, 'register.html')

def register_teacher(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        teacher_form = TeacherRegistrationForm(request.POST)
        if user_form.is_valid() and teacher_form.is_valid():
            user = user_form.save()
            teacher = teacher_form.save(commit=False)
            teacher.user = user
            teacher.save()
            login(request, user)
            return redirect('home')  # Redirigir al dashboard de profesores
    else:
        user_form = UserRegistrationForm()
        teacher_form = TeacherRegistrationForm()

    return render(request, 'register_teacher.html', {'user_form': user_form, 'teacher_form': teacher_form})

def register_student(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        student_form = StudentRegistrationForm(request.POST)
        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save()
            student = student_form.save(commit=False)
            student.user = user
            student.save()
            login(request, user)
            return redirect('home')  # Redirigir al dashboard de estudiantes
    else:
        user_form = UserRegistrationForm()
        student_form = StudentRegistrationForm()

    return render(request, 'register_student.html', {'user_form': user_form, 'student_form': student_form})
