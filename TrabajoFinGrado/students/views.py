from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from main.models import User

@login_required
def student_profile(request):
    # Verifica que el usuario es un estudiante
    if not request.user.is_student:
        return redirect('home')  # O alguna página de error o permiso denegado

    context = {
        'user': request.user,
    }
    return render(request, 'student/profile.html', context)
