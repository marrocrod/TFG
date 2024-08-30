from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, get_user_model, authenticate
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  # Corregido
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string

from datetime import datetime

from .forms import UserRegistrationForm, UserProfileForm, ChatForm, ExerciseGenerationForm, ExamGenerationForm, CustomAuthenticationForm, EmailUpdateForm  
from .models import User, Chat, Exam, Exercise, ExerciseSet, Event
from .tokens import account_activation_token  


import openai
import json



def home(request):
    context = {
        'message': "Bienvenido a la plataforma.",
        'user_type': "Guest"
    }

    if request.user.is_authenticated:
        user = request.user
        if user.user_type == "Teacher":
            # Filtros
            search_query = request.GET.get('search', '')
            degree_filters = request.GET.getlist('degrees')

            # Filtrar estudiantes por búsqueda
            students = User.objects.filter(user_type='Student').order_by('username')

            if search_query:
                students = students.filter(
                    Q(username__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(email__icontains=search_query)
                )
            
            if degree_filters:
                students = students.filter(degree__in=degree_filters)

            context.update({
                'message': "Bienvenido, Profesor.",
                'user_type': "Teacher",
                'students': students,
                'degrees': User.DegreeChoices.choices,  # Enviar los grados al contexto
                'selected_degrees': degree_filters,  # Enviar los grados seleccionados al contexto
                'search_query': search_query  # Enviar el término de búsqueda al contexto
            })
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'partials/student_list.html', {'students': students})

        elif user.user_type == "Student":
            # Obtener todos los exámenes del estudiante
            exams = user.exams.all().order_by('-created_at')

            # Obtener todos los conjuntos de ejercicios del estudiante
            exercise_sets = user.exercise_sets.all().order_by('-created_at')

            context.update({
                'message': "Bienvenido, Estudiante.",
                'user_type': "Student",
                'exercise_sets': exercise_sets,
                'exams': exams
            })
        else:
            context.update({
                'message': "Bienvenido.",
                'user_type': "Other"
            })
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
            user.is_active = False  # Desactivar la cuenta hasta la verificación
            user.save()
            
            # Enviar correo de activación
            current_site = get_current_site(request)
            mail_subject = 'Activate your Student account.'
            message = render_to_string('register/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()
            
            return render(request, 'register/registration_complete.html')  # Página de confirmación
    else:
        form = UserRegistrationForm()
    return render(request, 'register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'Teacher'
            user.is_active = False  # Desactivar la cuenta hasta la verificación
            user.save()
            
            # Enviar correo de activación
            current_site = get_current_site(request)
            mail_subject = 'Activate your Teacher account.'
            message = render_to_string('register/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()
            
            return render(request, 'register/registration_complete.html')  # Página de confirmación
    else:
        form = UserRegistrationForm()
    return render(request, 'register_teacher.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'register/account_activated.html')  # Página de éxito
    else:
        return render(request, 'register/activation_invalid.html')  # Página de error


class CustomLoginView(LoginView):
    User = get_user_model()
    form_class = CustomAuthenticationForm
    template_name = 'login.html'

    def post(self, request, *args, **kwargs):
        print("POST request received")
        
        form = self.get_form()

        # Obtener los datos del formulario
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Username: {username}")

        try:
            user = User.objects.get(username=username)
            print(f"Usuario encontrado: {user.username}, Activo: {user.is_active}")
            
            # Si el usuario está inactivo, mostramos el mensaje y no intentamos autenticar
            if not user.is_active:
                print("Cuenta inactiva detectada")
                context = self.get_context_data(form=form)
                context['inactive'] = True
                context['user_email'] = user.email
                return self.render_to_response(context)
        except User.DoesNotExist:
            print("Usuario no encontrado")
            # Continuamos para manejar el error de credenciales incorrectas
            pass

        # Si llegamos aquí, el usuario o no existe o está activo, intentamos autenticar
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print("Autenticación exitosa, iniciando sesión")
            login(request, user)
            return redirect(self.get_success_url())
        else:
            print("Autenticación fallida")
            form.add_error(None, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
        
        print("Formulario inválido, renderizando con errores")
        return self.form_invalid(form)

    def form_invalid(self, form):
        print("form_invalid llamado")
        print("Errores del formulario:", form.errors)
        return self.render_to_response(self.get_context_data(form=form))

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token

User = get_user_model()

def resend_activation_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user_id = request.session.get('user_id')

        print(f"Reenviar correo POST recibido, email: {email}, user_id: {user_id}")

        if user_id:
            user = User.objects.get(pk=user_id)

            # Verificar si el nuevo correo ya está en uso
            if User.objects.filter(email=email).exists():
                error_message = "Este correo electrónico ya está en uso."
                print("Correo electrónico ya en uso")
                return render(request, 'register/resend_activation_email.html', {
                    'error_message': error_message,
                    'email': email
                })
            else:
                user.email = email
                user.save()

                print("Correo electrónico actualizado y guardado")

                current_site = get_current_site(request)
                mail_subject = 'Activate your account.'
                message = render_to_string('register/acc_active_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                email_message = EmailMessage(mail_subject, message, to=[email])
                email_message.send()

                print("Correo de activación reenviado, redirigiendo a página de éxito")
                return redirect('activation_resent')
        
        print("No se encontró el user_id en la sesión, redirigiendo a login")
        return redirect('login')

    else:
        email = request.GET.get('email')
        user = User.objects.filter(email=email).first()

        print(f"GET recibido, email: {email}")

        if user and not user.is_active:
            # Guardar el user_id en la sesión para usarlo después
            request.session['user_id'] = user.pk
            print(f"Usuario encontrado y no activo, user_id: {user.pk}")
            return render(request, 'register/resend_activation_email.html', {'email': email})

    print("Redirigiendo a login desde GET")
    return redirect('login')




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


def session_expired(request):
    return render(request, 'session_expired.html', {
        'message': 'Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.',
    })


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



#############################################################
#############################################################
################# ---- ESTUDIANTES ---- #####################
#############################################################
#############################################################

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
                
                # Utiliza el modelo gpt-4o-mini con el endpoint correcto
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  # Cambiar el modelo aquí
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                generated_text = response['choices'][0]['message']['content'].strip()
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
def generate_exercises_view(request):
    user = request.user
    if user.user_type != 'Student':
        return redirect('home')

    # Obtener los conjuntos de ejercicios generados por el estudiante
    exercise_sets = user.exercise_sets.all().order_by('-created_at')

    return render(request, 'exercises.html', {
        'exercise_sets': exercise_sets
    })


@login_required
def generate_exam_view(request):
    user = request.user
    if user.user_type != 'Student':
        return redirect('home')

    # Obtener los exámenes generados por el estudiante
    exams = user.exams.all().order_by('-created_at')

    return render(request, 'exams.html', {
        'exams': exams
    })


@login_required
def generate_exam(request):
    if request.method == "POST":
        form = ExamGenerationForm(request.POST)
        if form.is_valid():
            exam_name = form.cleaned_data['exam_name']
            topic_1 = form.cleaned_data['topic_1']
            topic_2 = form.cleaned_data['topic_2']
            topic_3 = form.cleaned_data['topic_3']
            topic_4 = form.cleaned_data['topic_4']

            # Crear un nuevo examen
            exam = Exam.objects.create(student=request.user, name=exam_name)

            # Crear un nuevo set de ejercicios para este examen
            exercise_set = ExerciseSet.objects.create(student=request.user, name=exam_name)

            # Configuración de los ejercicios con los temas y las dificultades
            exercise_configs = [
                {'difficulty': 'Easy', 'topic': topic_1},
                {'difficulty': 'Easy', 'topic': topic_2},
                {'difficulty': 'Medium', 'topic': topic_3},
                {'difficulty': 'Hard', 'topic': topic_4}
            ]

            for config in exercise_configs:
                prompt = generate_prompt(config['topic'], config['difficulty'])

                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an assistant that generates educational content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                generated_text = response['choices'][0]['message']['content'].strip()
                statement, solution = parse_generated_text(generated_text)

                # Crear y guardar el ejercicio dentro del examen y asignar el exercise_set
                exercise = Exercise.objects.create(
                    student=request.user,
                    statement=statement,
                    solution=solution,
                    difficulty=config['difficulty'],
                    topic=config['topic'],
                    exercise_set=exercise_set  # Asigna el set de ejercicios
                )
                exercise.generate_html_content()

                exam.exercises.add(exercise)

            return redirect('exam_detail', exam_id=exam.exam_id)

    else:
        form = ExamGenerationForm()

    return render(request, 'generate_exam.html', {'form': form})


@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, exam_id=exam_id)
    
    # Verifica si el usuario es el estudiante dueño del examen o un profesor
    if exam.student != request.user and not request.user.is_teacher:
        return HttpResponseForbidden("No tienes permiso para acceder a este examen.")

    if exam.is_submitted:
        print(f"Examen {exam_id} ya fue entregado.")
        return redirect('archived_exam', exam_id=exam_id)
    
    if request.method == "POST" and 'submit_exam' in request.POST:
        print(f"Examen {exam_id} está siendo entregado.")
        return redirect('submit_exam', exam_id=exam_id)
    
    # Calcular el tiempo restante
    time_left = (exam.start_time + timezone.timedelta(minutes=90)) - timezone.now()
    time_left_seconds = max(time_left.total_seconds(), 0)
    print(f"Tiempo restante para el examen {exam_id}: {time_left_seconds} segundos")
    
    return render(request, 'exam_detail.html', {
        'exam': exam,
        'time_left': time_left_seconds,
    })



@login_required
def submit_exam(request, exam_id):
    print(f"Submit exam triggered for exam_id: {exam_id}")
    print("request.POST:", request.POST)  # Verifica todo lo que está en POST

    exam = get_object_or_404(Exam, exam_id=exam_id, student=request.user)
    exam.is_submitted = True
    exam.submission_time = timezone.now()

    for exercise in exam.exercises.all():
        student_solution_key = f'student_solution_{exercise.exercise_id}'
        student_solution_value = request.POST.get(student_solution_key)
        print(f"Received solution for {student_solution_key}: {student_solution_value}")

        if student_solution_value:
            # Asegúrate de asignar correctamente el valor antes de guardar
            exercise.student_solution = student_solution_value
            
            prompt = f"""Estoy haciendo ejercicios de un examen y quiero evaluar la solución del siguiente ejercicio:

            Enunciado del ejercicio:
            {exercise.statement}

            Solución del alumno:
            {student_solution_value}

            Solución esperada por el profesor:
            {exercise.solution}

            Responde únicamente con "correcto" o "incorrecto" en función de si el programa que 
            te he pasado es correcto o no respecto al enunciado y a la solución que se pide y dame
            una breve explicación si es necesario para señalar los fallos o aciertos del código."""

            print("Sending prompt to OpenAI...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un asistente educativo."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            evaluation = response['choices'][0]['message']['content'].strip().lower()
            print(f"OpenAI evaluation result: {evaluation}")

            # Solo marcar como correcto si la evaluación empieza con "correcto"
            if evaluation.startswith("correcto"):
                exercise.is_correct = True
                if exercise in exam.exercises.all()[:2]:
                    exercise.score = 1.5
                elif exercise == exam.exercises.all()[2]:
                    exercise.score = 2.75
                elif exercise == exam.exercises.all()[3]:
                    exercise.score = 4.25
            else:
                exercise.is_correct = False
                exercise.score = 0.0

        else:
            print(f"No solution provided for exercise ID: {exercise.exercise_id}. Skipping OpenAI evaluation.")
            exercise.is_correct = False
            exercise.score = 0.0
            exercise.student_solution = ""  # Guarda una cadena vacía si no hay solución

        # Aquí es donde se guarda el ejercicio, asegurémonos de que el valor esté correcto
        print(f"Saving exercise {exercise.exercise_id} with solution: {exercise.student_solution}")
        exercise.save()

    exam.save()
    total_score = exam.grade
    print(f"Total score calculated: {total_score}")

    return render(request, 'archived_exam.html', {'exam': exam, 'total_score': total_score})




@login_required
def archived_exam(request, exam_id):
    exam = get_object_or_404(Exam, exam_id=exam_id, is_submitted=True)
    
    # Verificar que el usuario es el estudiante propietario del examen o un profesor
    if request.user != exam.student and not request.user.is_teacher:
        return HttpResponseForbidden("No tienes permiso para acceder a este examen.")
    
    total_score = exam.grade
    return render(request, 'archived_exam.html', {'exam': exam, 'total_score': total_score})


def calendar_view(request):
    return render(request, 'calendar.html')


@login_required
def calendar_events(request):
    events = Event.objects.filter(user=request.user)  # Filtrar por usuario
    events_list = []
    for event in events:
        events_list.append({
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'color': event.color,  # Añadir color al evento
        })
    return JsonResponse(events_list, safe=False)

@csrf_exempt
def create_event(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        event = Event.objects.create(
            title=data['title'],
            start_time=data['start'],
            end_time=data['end']
        )
        return JsonResponse({'status': 'Event Created'}, status=201)



@login_required
def day_view(request, date):
    # Convertir la fecha de la URL en un objeto datetime
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Filtrar los eventos del usuario que ha iniciado sesión y la fecha específica
    events = Event.objects.filter(start_time__date=date_obj, user=request.user)
    
    if request.method == 'POST':
        # Manejar la creación de un nuevo evento
        title = request.POST.get('title')
        start_time = f"{date} {request.POST.get('start_time')}"
        end_time = f"{date} {request.POST.get('end_time')}"
        color = request.POST.get('color')

        Event.objects.create(
            title=title,
            start_time=start_time,
            end_time=end_time,
            color=color,
            user=request.user  # Asignar el evento al usuario actual
        )

    return render(request, 'day_view.html', {'date': date, 'events': events})



#############################################################
#############################################################
################# ---- PROFESORES ---- ######################
#############################################################
#############################################################

@login_required
def student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id, user_type='Student')
    
    if not request.user.is_teacher:
        return HttpResponseForbidden("No tienes permiso para acceder a este contenido.")

    archived_chats = Chat.objects.filter(student=student, is_archived=True).order_by('-last_activity')

    archived_exams = Exam.objects.filter(student=student, is_submitted=True).order_by('-submission_time')

    context = {
        'student': student,
        'archived_chats': archived_chats,
        'archived_exams': archived_exams,
    }
    
    return render(request, 'student_detail.html', context)




