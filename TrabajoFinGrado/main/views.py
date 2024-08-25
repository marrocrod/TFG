from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.http import HttpResponseForbidden

from .forms import UserRegistrationForm, UserProfileForm, ChatForm, ExerciseGenerationForm
from .models import Chat, Exam, Exercise, ExerciseSet

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


@login_required
def generate_exercises(request):
    if request.method == "POST":
        form = ExerciseGenerationForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            difficulty = form.cleaned_data['difficulty']
            number_of_exercises = int(form.cleaned_data['number_of_exercises'])
            set_name = form.cleaned_data['set_name']  # Recoge el nombre del conjunto

            # Crear un nuevo ExerciseSet con el nombre proporcionado
            exercise_set = ExerciseSet.objects.create(student=request.user, name=set_name)

            for _ in range(number_of_exercises):
                prompt = generate_prompt(topic, difficulty)
                
                # Utiliza el modelo gpt-3.5-instruct
                response = openai.Completion.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.7
                )
                generated_text = response.choices[0].text.strip()
                statement, solution = parse_generated_text(generated_text)
                
                # Crear y guardar el ejercicio dentro del set
                exercise = Exercise.objects.create(
                    exercise_set=exercise_set,
                    student=request.user,
                    statement=statement,
                    solution=solution,
                    difficulty=difficulty,
                    topic=topic
                )
                exercise.generate_html_content()

            return redirect('exercise_set_detail', set_id=exercise_set.set_id)  # Redirigir a la vista del conjunto de ejercicios

    else:
        form = ExerciseGenerationForm()

    return render(request, 'generate_exercises.html', {'form': form})


def generate_prompt(topic, difficulty):
    # Define la explicación previa sobre los niveles de dificultad
    difficulty_explanation = {
        'Easy': "El ejercicio debe ser sencillo, adecuado para principiantes, y no requerir conocimientos avanzados. Como mucho se podrá resolver en 10 minutos.",
        'Medium': "El ejercicio debe tener un nivel intermedio de dificultad, adecuado para estudiantes con conocimientos básicos de programación. Deberá poder resolverse en 20 minutos máximo.",
        'Hard': "El ejercicio debe ser desafiante, adecuado para estudiantes avanzados y requerir un entendimiento profundo del tema. Como máximo deberá poder resolverse en alrededor de 30m."
    }
    
    # Define diferentes prompts en función del tema seleccionado
    topic_prompts = {
        1: f"Genera un ejercicio de programación en Python sobre estructuras de datos.",
        2: f"Genera un ejercicio de programación en Python sobre algoritmos de ordenación.",
        3: f"Genera un ejercicio de programación en Python sobre recursividad.",
        4: f"Genera un ejercicio de programación en Python sobre estructuras de control.",
        5: f"Genera un ejercicio de programación en Python sobre manipulación de cadenas.",
        6: f"Genera un ejercicio de programación en Python sobre manejo de archivos.",
        7: f"Genera un ejercicio de programación en Python sobre manejo de excepciones."
    }

    # Combina la explicación del nivel de dificultad con el prompt del tema
    prompt = f"{difficulty_explanation[difficulty]} {topic_prompts.get(topic, 'Genera un ejercicio de programación en Python.')}"
    
    # Añadir la instrucción para incluir "Código de la solución:" antes de la solución
    prompt += " Después del enunciado, proporcione la solución en formato de código. Asegúrese de incluir 'Solución:' antes del código de la solución, ya que lo necesito en dicho formato"

    return prompt


def parse_generated_text(generated_text):
    # Buscamos el indicador "Código del programa:" para separar el enunciado de la solución
    solution_split_keyword = "Solución:"
    if solution_split_keyword in generated_text:
        parts = generated_text.split(solution_split_keyword)
        statement = parts[0].strip()
        solution = parts[1].strip() if len(parts) > 1 else ""
    else:
        # Si no se encuentra la palabra clave, asumimos que todo es parte del enunciado
        statement = generated_text.strip()
        solution = ""  # No se proporciona solución

    return statement, solution


@login_required
def exercise_set_detail(request, set_id):
    exercise_set = get_object_or_404(ExerciseSet, set_id=set_id, student=request.user)
    exercises = exercise_set.exercises.all()
    return render(request, 'exercise_set_detail.html', {'exercise_set': exercise_set, 'exercises': exercises})


@login_required
def generate_exam(request):
    if request.method == "POST":
        form = ExerciseGenerationForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            difficulty = form.cleaned_data['difficulty']
            number_of_exercises = int(form.cleaned_data['number_of_exercises'])

            # Crear un nuevo examen
            exam = Exam.objects.create(student=request.user)

            for _ in range(number_of_exercises):
                prompt = generate_prompt(topic, difficulty)
                response = openai.Completion.create(
                    engine="gpt-4o-mini",
                    prompt=prompt,
                    max_tokens=500
                )
                generated_text = response.choices[0].text.strip()
                statement, solution = parse_generated_text(generated_text)

                exercise = Exercise.objects.create(
                    student=request.user,
                    statement=statement,
                    solution=solution,
                    difficulty=difficulty,
                    topic=topic
                )
                exercise.generate_html_content()
                exam.exercises.add(exercise)

            return redirect('exam_detail', exam_id=exam.exam_id)  # Redirigir a una vista que muestre el examen

    else:
        form = ExerciseGenerationForm()

    return render(request, 'generate_exam.html', {'form': form})

@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, exam_id=exam_id, student=request.user)
    exercises = exam.exercises.all()
    return render(request, 'exam_detail.html', {'exam': exam, 'exercises': exercises})
