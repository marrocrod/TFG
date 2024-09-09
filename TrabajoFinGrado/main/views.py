from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, get_user_model, authenticate
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string

from datetime import datetime, timedelta

from .forms import UserRegistrationForm, UserProfileForm, ChatForm, ExerciseGenerationForm, ExamGenerationForm, CustomAuthenticationForm, EmailUpdateForm, ForumForm, CommentForm  
from .models import User, Chat, Exam, Exercise, ExerciseSet, Event, Forum, Comment
from .tokens import account_activation_token  


import openai
import json


#~~~~~~~~HOME~~~~~~~~
def home(request):

    delete_unactivated_users()

    context = {
        'message': "Bienvenido a la plataforma.",
        'user_type': "Guest"
    }

    if request.user.is_authenticated:
        user = request.user
        if user.user_type == "Teacher" and request.user.verification_status == 'APPROVED':
            search_query = request.GET.get('search', '')
            degree_filters = request.GET.getlist('degrees')

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
                'degrees': User.DegreeChoices.choices,  
                'selected_degrees': degree_filters,  
                'search_query': search_query  
            })
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'partials/student_list.html', {'students': students})
        
        elif request.user.user_type == 'Teacher' and request.user.verification_status == 'PENDING':
            return redirect('pending_teacher')

        elif user.user_type == "Student":
            exams = user.exams.all().order_by('-created_at')

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

#~~~~~~~~PERMISSONS~~~~~~~~

def no_permission(request):
    return render(request, 'no_permission.html', {
        'message': 'No tienes permiso para acceder a este contenido.'
    })

def content_for_students_only(request):
    return render(request, 'content_for_students_only.html', {
        'message': 'Este contenido es solo para alumnos.'
    })


#~~~~~~~~REGISTERS~~~~~~~~

def register(request):
    return render(request, 'register/register.html')


def register_student(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'Student'
            user.is_active = False  
            user.save()
            
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
            
            return render(request, 'register/registration_complete.html')  
    else:
        form = UserRegistrationForm()
    return render(request, 'register/register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'Teacher'
            user.verification_status = 'PENDING'  
            user.is_active = False  
            user.save()
            
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
            
            return render(request, 'register/registration_complete.html')  
    else:
        form = UserRegistrationForm()
    return render(request, 'register/register_teacher.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'register/account_activated.html')  
    else:
        return render(request, 'register/activation_invalid.html') 
    

User = get_user_model()

def resend_activation_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user_id = request.session.get('user_id')

        print(f"Reenviar correo POST recibido, email: {email}, user_id: {user_id}")

        if user_id:
            user = User.objects.get(pk=user_id)

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
            request.session['user_id'] = user.pk
            print(f"Usuario encontrado y no activo, user_id: {user.pk}")
            return render(request, 'register/resend_activation_email.html', {'email': email})

    print("Redirigiendo a login desde GET")
    return redirect('login')

#~~~~~~~~LOGIN~~~~~~~~

class CustomLoginView(LoginView):
    User = get_user_model()
    form_class = CustomAuthenticationForm
    template_name = 'login.html'

    def post(self, request, *args, **kwargs):
        delete_unactivated_users()
        print("POST request received")
    
        form = self.get_form()
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Username: {username}")

        try:
            user = User.objects.get(username=username)
            print(f"Usuario encontrado: {user.username}, Activo: {user.is_active}")
        
            if not user.is_active:
                print("Cuenta inactiva detectada")
                context = self.get_context_data(form=form)
                context['inactive'] = True
                context['user_email'] = user.email
                return self.render_to_response(context)
        except User.DoesNotExist:
            print("Usuario no encontrado")
            pass

        user = authenticate(request, username=username, password=password)
        if user is not None:
            print("Autenticación exitosa, iniciando sesión")
            login(request, user)
            return redirect(self.get_success_url())
        else:
            print("Autenticación fallida")
            if not form.non_field_errors():
                form.add_error(None, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
    
        print("Formulario inválido, renderizando con errores")
        return self.form_invalid(form)


#~~~~~~~~PROFILE~~~~~~~~

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
            return redirect('user_profile')  
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form})

#~~~~~~~~FORUM~~~~~~~~

@login_required
def forum_home(request):
    # Consulta los foros que no están cerrados y ordénalos por fecha de creación
    open_forums = Forum.objects.filter(is_closed=False).order_by('-created_at')
    
    # Consulta los foros que están cerrados y ordénalos por fecha de creación
    closed_forums = Forum.objects.filter(is_closed=True).order_by('-created_at')
    
    # Concatenamos ambas listas: primero los abiertos, luego los cerrados
    all_forums = list(open_forums) + list(closed_forums)

    # Los foros recientes solo incluyen los que están abiertos
    recent_forums = open_forums[:5]
    
    context = {
        'recent_forums': recent_forums,
        'all_forums': all_forums,
    }
    return render(request, 'forum/forum_home.html', context)

@login_required
def create_forum(request):
    if request.method == 'POST':
        form = ForumForm(request.POST, request.FILES)
        if form.is_valid():
            forum = form.save(commit=False)
            forum.created_by = request.user
            forum.save()
            return redirect('forum_home')
    else:
        form = ForumForm()
    return render(request, 'forum/create_forum.html', {'form': form})

@login_required
def view_forum(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    comments = forum.comments.all().order_by('created_at')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.forum = forum
            comment.user = request.user
            comment.save()
            return redirect('view_forum', forum_id=forum.id)
    else:
        form = CommentForm()
    context = {
        'forum': forum,
        'comments': comments,
        'form': form,
    }
    return render(request, 'forum/view_forum.html', context)

@login_required
def close_forum(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id, created_by=request.user)
    forum.is_closed = True
    forum.save()
    return redirect('view_forum', forum_id=forum_id)

#############################################################
#############################################################
################# ---- ESTUDIANTES ---- #####################
#############################################################
#############################################################

#~~~~~~~~TEACHERS_LIST~~~~~~~~

@login_required
def teacher_list(request):
    if not request.user.is_student:
        return redirect('home')  
    
    teachers = User.objects.filter(user_type='Teacher')

    context = {
        'teachers': teachers,
    }

    return render(request, 'teacher_list.html', context)

#~~~~~~~~CHAT~~~~~~~~

openai.api_key = settings.OPENAI_API_KEY

@login_required
def chat_view(request, chat_id=None):
    if chat_id is None:
        chat = Chat.objects.filter(student=request.user, is_archived=False).order_by('-last_activity').first()

        if chat:
            return redirect('chat', chat_id=chat.chat_id)
        else:
            chat = Chat.objects.create(student=request.user, conversation=json.dumps([]))
            return redirect('chat', chat_id=chat.chat_id)
    else:
        chat = get_object_or_404(Chat, chat_id=chat_id)
        print(f"Chat ID: {chat.chat_id}, Conversation at load: {chat.get_conversation()}")

        if chat.is_archived:
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
                model="gpt-4o-mini",  
                messages=chat.get_conversation()
            )
            response_text = response['choices'][0]['message']['content']

            chat.add_message(role="assistant", content=response_text)
            print(f"Chat ID: {chat.chat_id}, Updated conversation after adding assistant response: {chat.get_conversation()}")

    else:
        form = ChatForm()

    return render(request, 'chat/chat.html', {'form': form, 'chat': chat})


@login_required
def archive_chat(request, chat_id):
    chat = get_object_or_404(Chat, chat_id=chat_id)

    if request.user != chat.student and request.user.user_type != 'Teacher':
        return HttpResponseForbidden("No tienes permiso para archivar este chat.")

    chat.is_archived = True
    chat.save()
    return redirect('archived_chat', chat_id=chat.chat_id)

@login_required
def archived_chat_view(request, chat_id):
    chat = get_object_or_404(Chat, chat_id=chat_id)
    
    if request.user != chat.student and request.user.user_type != 'Teacher':
        return HttpResponseForbidden("No tienes permiso para acceder a este chat.")
    
    context = {
        'chat': chat
    }
    return render(request, 'chat/archived_chat.html', context)


@login_required
def archived_chats_list(request):
    if request.user.user_type == 'Teacher':
        chats = Chat.objects.filter(is_archived=True)
    else:
        chats = Chat.objects.filter(is_archived=True, student=request.user)

    return render(request, 'chat/archived_chats_list.html', {'chats': chats})

#~~~~~~~~EXERCISES~~~~~~~~

@login_required
def generate_exercises(request):
    if request.method == "POST":
        form = ExerciseGenerationForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            difficulty = form.cleaned_data['difficulty']
            number_of_exercises = int(form.cleaned_data['number_of_exercises'])
            set_name = form.cleaned_data['set_name']  

            exercise_set = ExerciseSet.objects.create(student=request.user, name=set_name)

            for _ in range(number_of_exercises):
                prompt = generate_prompt(topic, difficulty)
                
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                generated_text = response['choices'][0]['message']['content'].strip()
                statement, solution = parse_generated_text(generated_text)
                
                exercise = Exercise.objects.create(
                    exercise_set=exercise_set,
                    student=request.user,
                    statement=statement,
                    solution=solution,
                    difficulty=difficulty,
                    topic=topic
                )
                exercise.generate_html_content()

            return redirect('exercise_set_detail', set_id=exercise_set.set_id)  

    else:
        form = ExerciseGenerationForm()

    return render(request, 'exercise/generate_exercises.html', {'form': form})



def generate_prompt(topic, difficulty):
    difficulty_explanation = {
        'Easy': "El ejercicio debe ser sencillo, adecuado para principiantes, y no requerir conocimientos avanzados. Como mucho se podrá resolver en 10 minutos.",
        'Medium': "El ejercicio debe tener un nivel intermedio de dificultad, adecuado para estudiantes con conocimientos básicos de programación. Deberá poder resolverse en 20 minutos máximo.",
        'Hard': "El ejercicio debe ser desafiante, adecuado para estudiantes avanzados y requerir un entendimiento profundo del tema. Como máximo deberá poder resolverse en alrededor de 30m."
    }
    
    # Define diferentes prompts en función del tema seleccionado
    topic_prompts = {
        1: f"Genera un ejercicio de programación en Python que cubra el tema de 'Instrucciones y funciones'. Este tema abarca el uso de sentencias y funciones predefinidas, como print, la definición de funciones personalizadas, el uso de comentarios y la estructura básica de un programa en Python. Se deberá pedir al estudiante que defina una función con parámetros, que utilice instrucciones sencillas como asignaciones o bucles, y que explique con comentarios cada parte de la función.",
        2: f"Genera un ejercicio de programación en Python que cubra el tema de 'Expresiones y tipos'. Este tema trata sobre el uso de expresiones, operadores aritméticos, y variables en Python. Se debe pedir que el estudiante resuelva un ejercicio utilizando operadores y expresiones para manipular variables y tipos básicos de datos (números, cadenas, booleanos).",
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
    return render(request, 'exercise/exercise_set_detail.html', {'exercise_set': exercise_set, 'exercises': exercises})


@login_required
def generate_exercises_view(request):
    user = request.user
    if user.user_type != 'Student':
        return redirect('home')

    # Obtener los ExerciseSet relacionados con los ejercicios que están en exámenes
    exam_exercise_sets = Exam.objects.filter(student=request.user).values_list('exercises__exercise_set', flat=True)

    # Excluir los ExerciseSet que están relacionados con exámenes
    exercise_sets = user.exercise_sets.exclude(set_id__in=exam_exercise_sets).order_by('-created_at')

    return render(request, 'exercise/exercises.html', {
        'exercise_sets': exercise_sets
    })




#~~~~~~EXAMS~~~~~~~~

@login_required
def generate_exam_view(request):
    user = request.user
    if user.user_type != 'Student':
        return redirect('home')

    exams = user.exams.all().order_by('-created_at')

    return render(request, 'exam/exams.html', {
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
                        {"role": "system", "content": "Eres un asistente que está generando contenido educacional para universitarios que están aprendiendo a programar en Python"},
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

    return render(request, 'exam/generate_exam.html', {'form': form})


@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, exam_id=exam_id)
    
    if exam.student != request.user and not request.user.is_teacher:
        return HttpResponseForbidden("No tienes permiso para acceder a este examen.")

    if exam.is_submitted:
        return redirect('archived_exam', exam_id=exam_id)
    
    if request.method == "POST" and 'submit_exam' in request.POST:
        return redirect('submit_exam', exam_id=exam_id)
    
    time_left = (exam.start_time + timezone.timedelta(minutes=90)) - timezone.now()
    time_left_seconds = max(time_left.total_seconds(), 0)
    
    return render(request, 'exam/exam_detail.html', {
        'exam': exam,
        'time_left': time_left_seconds,
    })



@login_required
def submit_exam(request, exam_id):
    print("request.POST:", request.POST)  

    exam = get_object_or_404(Exam, exam_id=exam_id, student=request.user)
    exam.is_submitted = True
    exam.submission_time = timezone.now()

    for exercise in exam.exercises.all():
        student_solution_key = f'student_solution_{exercise.exercise_id}'
        student_solution_value = request.POST.get(student_solution_key)

        if student_solution_value:
            exercise.student_solution = student_solution_value
            
            prompt = f"""Estoy haciendo ejercicios de un examen y quiero evaluar la solución del siguiente ejercicio:

            Enunciado del ejercicio:
            {exercise.statement}

            Solución del alumno:
            {student_solution_value}

            Solución esperada por el profesor:
            {exercise.solution}

            Responde únicamente con "correcto" o "incorrecto" en función de si el programa que 
            te he pasado es correcto o no respecto al enunciado que se propone y a la solución que se pide y dame
            una breve explicación si es necesario para señalar los fallos o aciertos del código."""

            print("Sending prompt to OpenAI...")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un asistente educativo que tiene que evaluar el resultado un ejercicio dado el enunciado de un ejercicio, la solución que ha proporcionado el alumno y la solución que ha generado una IA como posible solución del ejercicio."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            evaluation = response['choices'][0]['message']['content'].strip().lower()

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
            exercise.is_correct = False
            exercise.score = 0.0
            exercise.student_solution = ""  

        exercise.save()

    exam.save()
    total_score = exam.grade

    return render(request, 'exam/archived_exam.html', {'exam': exam, 'total_score': total_score})




@login_required
def archived_exam(request, exam_id):
    exam = get_object_or_404(Exam, exam_id=exam_id, is_submitted=True)
    
    if request.user != exam.student and not request.user.is_teacher:
        return HttpResponseForbidden("No tienes permiso para acceder a este examen.")
    
    total_score = exam.grade
    return render(request, 'exam/archived_exam.html', {'exam': exam, 'total_score': total_score})



#~~~~ CALENDARIO ~~~~~~
def calendar_view(request):
    now = timezone.now()
    thirty_days_from_now = now + timedelta(days=30)
    
    upcoming_events = Event.objects.filter(
        user=request.user,
        start_time__gte=now,
        start_time__lte=thirty_days_from_now
    ).order_by('start_time')
    
    context = {
        'upcoming_events': upcoming_events
    }
    return render(request, 'calendar/calendar.html', context)



@login_required
def calendar_events(request):
    events = Event.objects.filter(user=request.user)  
    events_list = []
    for event in events:
        events_list.append({
            'id': event.id,  
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'color': event.color,  
        })
    return JsonResponse(events_list, safe=False)

from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Event

@csrf_exempt
def create_event(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        start_time = parse_datetime(data['start'])
        end_time = parse_datetime(data['end'])
        
        if end_time <= start_time:
            return JsonResponse({'status': 'error', 'message': 'La hora de finalización debe ser posterior a la hora de inicio.'}, status=400)
        
        event = Event.objects.create(
            title=data['title'],
            start_time=start_time,
            end_time=end_time,
            color=data.get('color', '#000000')  
        )
        
        return JsonResponse({'status': 'Event Created', 'event_id': event.id}, status=201)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)


@login_required
def day_view(request, date):
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    
    events = Event.objects.filter(start_time__date=date_obj, user=request.user)
    error_message = None  
    
    if request.method == 'POST':
        title = request.POST.get('title')
        start_time = f"{date} {request.POST.get('start_time')}"
        end_time = f"{date} {request.POST.get('end_time')}"
        color = request.POST.get('color')

        
        if end_time <= start_time:
            error_message = "La hora de finalización debe ser posterior a la hora de inicio."
        else:
            
            Event.objects.create(
                title=title,
                start_time=start_time,
                end_time=end_time,
                color=color,
                user=request.user  
            )
            return redirect('calendar')

    return render(request, 'calendar/day_view.html', {'date': date, 'events': events, 'error_message': error_message})


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)
    error_message = None

    if request.method == 'POST':
        if 'save_changes' in request.POST:
            title = request.POST.get('title')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            color = request.POST.get('color')

            if end_time <= start_time:
                error_message = "La hora de finalización debe ser posterior a la hora de inicio."
            else:
                event.title = title
                event.start_time = start_time
                event.end_time = end_time
                event.color = color
                event.save()
                return redirect('calendar')
        
        elif 'delete_event' in request.POST:
            return redirect('delete-event', event_id=event.id)

    return render(request, 'calendar/edit_event.html', {'event': event, 'error_message': error_message})




@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    if request.method == 'POST':
        event.delete()
        return redirect('calendar')

    return render(request, 'calendar/delete_event.html', {'event': event})

def delete_unactivated_users():
    expiration_time = timezone.now() - timezone.timedelta(minutes=30)
    unactivated_users = User.objects.filter(is_active=False, created_at__lt=expiration_time)
    unactivated_users.delete()


#############################################################
#############################################################
################# ---- PROFESORES ---- ######################
#############################################################
#############################################################

@login_required
def pending_teacher(request):
    if request.user.verification_status == 'PENDING' and request.user.user_type == 'Teacher':
        return render(request, 'pending_teacher.html')
    return redirect('home')  

@login_required
def rejected_teacher(request):
    return render(request, 'rejected_teacher.html')


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




