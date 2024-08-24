from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.http import HttpResponseForbidden

from .forms import UserRegistrationForm, UserProfileForm, ChatForm
from .models import Chat

import openai
import json





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

@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_profile')  # Redirige al perfil del usuario tras guardar los cambios
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form})


openai.api_key = settings.OPENAI_API_KEY

@login_required
def chat_view(request, chat_id=None):
    if chat_id is None:
        # Buscar la última conversación no archivada del usuario
        chat = Chat.objects.filter(student=request.user, is_archived=False).order_by('-last_activity').first()

        if chat:
            # Si hay una conversación no archivada, redirigir a ella
            return redirect('chat', chat_id=chat.chat_id)
        else:
            # Si todas las conversaciones están archivadas, crear una nueva conversación y redirigir a ella
            chat = Chat.objects.create(student=request.user, conversation=json.dumps([]))
            return redirect('chat', chat_id=chat.chat_id)
    else:
        chat = get_object_or_404(Chat, chat_id=chat_id)
        print(f"Chat ID: {chat.chat_id}, Conversation at load: {chat.get_conversation()}")

        if chat.is_archived:
            # Si el chat está archivado, redirigir a la vista del chat archivado
            return redirect('archived_chat', chat_id=chat_id)

        if request.user != chat.student and request.user.user_type != 'Teacher':
            return HttpResponseForbidden("No tienes permiso para acceder a este chat.")

    if request.method == "POST":
        form = ChatForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['user_input']
            print(f"Chat ID: {chat.chat_id}, Conversation before adding user message: {chat.get_conversation()}")

            chat.add_message(role="user", content=user_input)
            print(f"Chat ID: {chat.chat_id}, Conversation after adding user message: {chat.get_conversation()}")

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Asegúrate de utilizar el modelo correcto
                messages=chat.get_conversation()
            )
            response_text = response['choices'][0]['message']['content']

            chat.add_message(role="assistant", content=response_text)
            print(f"Chat ID: {chat.chat_id}, Updated conversation after adding assistant response: {chat.get_conversation()}")

    else:
        form = ChatForm()

    return render(request, 'chat.html', {'form': form, 'chat': chat})






@login_required
def archive_chat(request, chat_id):
    chat = get_object_or_404(Chat, chat_id=chat_id)

    # Verificar que solo el estudiante que creó el chat o un profesor puede archivarlo
    if request.user != chat.student and request.user.user_type != 'Teacher':
        return HttpResponseForbidden("No tienes permiso para archivar este chat.")

    # Marcar el chat como archivado
    chat.is_archived = True
    chat.save()
    return redirect('archived_chat', chat_id=chat.chat_id)

@login_required
def archived_chat_view(request, chat_id):
    # Obtener el chat correspondiente al chat_id
    chat = get_object_or_404(Chat, chat_id=chat_id)
    
    # Verificar que el usuario sea el estudiante que creó el chat o un profesor
    if request.user != chat.student and request.user.user_type != 'Teacher':
        return HttpResponseForbidden("No tienes permiso para acceder a este chat.")
    
    # Renderizar la conversación guardada
    context = {
        'chat': chat
    }
    return render(request, 'archived_chat.html', context)


@login_required
def archived_chats_list(request):
    # Verificar si el usuario es un profesor
    if request.user.user_type == 'Teacher':
        # El profesor puede ver todos los chats archivados
        chats = Chat.objects.filter(is_archived=True)
    else:
        # El estudiante solo puede ver sus propios chats archivados
        chats = Chat.objects.filter(is_archived=True, student=request.user)

    return render(request, 'archived_chats_list.html', {'chats': chats})


