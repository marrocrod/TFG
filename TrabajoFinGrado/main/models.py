from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
import json
from datetime import datetime, timedelta
from django.utils import timezone


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True) 
    email = models.EmailField(unique=True) 

    class DegreeChoices(models.TextChoices):
        SOFTWARE_ENGINEERING = 'Software Engineering'
        HEALTH_ENGINEERING = 'Health Engineering'
        COMPUTER_ENGINEERING = 'Computer Engineering'
    
    degree = models.CharField(max_length=100, choices=DegreeChoices.choices)

    class UserTypeChoices(models.TextChoices):
        TEACHER = 'Teacher'
        STUDENT = 'Student'

    user_type = models.CharField(max_length=10, choices=UserTypeChoices.choices)

    class GroupChoices(models.TextChoices):
        GROUP_1 = 'Grupo 1'
        GROUP_2 = 'Grupo 2'
        GROUP_3 = 'Grupo 3'
        GROUP_4 = 'Grupo 4'

    group = models.CharField(max_length=50, choices=GroupChoices.choices, verbose_name='Group')

    # Nuevo campo para la verificación del estado
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        
    verification_status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.APPROVED  # Default a APPROVED para estudiantes
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='users_with_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    @property
    def is_teacher(self):
        return self.user_type == "Teacher"

    @property
    def is_student(self):
        return self.user_type == "Student"


class ExerciseSet(models.Model):
    set_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_sets')
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, default="Conjunto de Ejercicios")
    is_archived = models.BooleanField(default=False)  # Nuevo campo para archivado

    def __str__(self):
        return f"{self.name} - {self.student.username} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"



class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    exercise_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercises', limit_choices_to=Q(user_type='Student'))
    statement = models.TextField()
    solution = models.TextField()
    student_solution = models.TextField(blank=True, null=True)  # Solución proporcionada por el alumno
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    topic = models.IntegerField(choices=[(i, f'Tema {i}') for i in range(1, 8)])
    html_content = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    exercise_set = models.ForeignKey(ExerciseSet, on_delete=models.CASCADE, related_name='exercises')  # Asegúrate de que este campo está definido si es necesario

    def generate_html_content(self):
        self.html_content = f"""
        <div class="exercise">
            <h3>Ejercicio {self.exercise_id}</h3>
            <p>{self.statement}</p>
            <button onclick="toggleSolution({self.exercise_id})">Mostrar solución</button>
            <div id="solution_{self.exercise_id}" style="display:none;">
                <pre>{self.solution}</pre>
            </div>
            <div class="code-editor">
                <textarea id="editor_{self.exercise_id}"></textarea>
                <button onclick="runCode({self.exercise_id})">Ejecutar código</button>
                <div id="output_{self.exercise_id}"></div>
            </div>
        </div>
        """
        self.save()

    def __str__(self):
        return f"Exercise {self.exercise_id} - {self.difficulty} - Tema {self.topic}"

class Exam(models.Model):
    exam_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams', limit_choices_to=Q(user_type='Student'))
    name = models.CharField(max_length=100)
    start_time = models.DateTimeField(default=timezone.now)
    submission_time = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    exercises = models.ManyToManyField('Exercise', related_name='exams')
    created_at = models.DateTimeField(auto_now_add=True)  # Campo para la fecha de creación

    @property
    def grade(self):
        return sum(exercise.score for exercise in self.exercises.all() if exercise.is_correct)

    @property
    def is_time_over(self):
        return timezone.now() > self.start_time + timezone.timedelta(minutes=90)


class Chat(models.Model):
    chat_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats', limit_choices_to=Q(user_type='Student'))
    url = models.URLField()
    conversation = models.TextField(default="")
    is_archived = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)  # Se actualiza con cada mensaje nuevo

    def add_message(self, role, content):
        # Cargar la conversación existente
        if self.conversation:
            convo = json.loads(self.conversation)
        else:
            convo = []
    
        # Imprimir la conversación antes de agregar el nuevo mensaje
        print(f"Conversation before adding new message: {convo}")
    
        convo.append({"role": role, "content": content})
    
        # Convertir de nuevo la lista a JSON y guardar en la conversación
        self.conversation = json.dumps(convo)
    
        # Imprimir la conversación después de agregar el nuevo mensaje
        print(f"Updated conversation: {self.conversation}")
    
        # Actualizar la última actividad
        self.last_activity = datetime.now()
    
        # Guardar el modelo para persistir los cambios
        self.save()


    def get_conversation(self):
        if self.conversation:
            return json.loads(self.conversation)
        return []

    def __str__(self):
        return f"Chat with {self.student.username}"
    

class Event(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    color = models.CharField(max_length=7, default='#000000')  # Campo para el color del evento
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')  # Relación con el usuario

    def __str__(self):
        return self.title

class Forum(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    image = models.ImageField(upload_to='forum_images/', blank=True, null=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.forum.title}'