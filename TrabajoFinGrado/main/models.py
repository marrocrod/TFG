from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
import json
from datetime import datetime



class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)

    class DegreeChoices(models.TextChoices):
        SOFTWARE_ENGINEERING = 'Software Engineering'
        HEALTH_ENGINEERING = 'Health Engineering'
        COMPUTER_ENGINEERING = 'Computer Engineering'
    
    degree = models.CharField(max_length=100, choices=DegreeChoices.choices)

    class UserTypeChoices(models.TextChoices):
        TEACHER = 'Teacher'
        STUDENT = 'Student'

    user_type = models.CharField(max_length=10, choices=UserTypeChoices.choices)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='users_in_auth_groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
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

class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    groups = models.ManyToManyField('Group', related_name='courses_in')

class Group(models.Model):
    group_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups_in_course')
    teachers = models.ManyToManyField(User, related_name='teaching_groups', limit_choices_to=Q(user_type='Teacher'))
    students = models.ManyToManyField(User, related_name='student_groups', limit_choices_to=Q(user_type='Student'))

class Subgroup(models.Model):
    subgroup_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='subgroups')
    teachers = models.ManyToManyField(User, related_name='teaching_subgroups', limit_choices_to=Q(user_type='Teacher'))
    students = models.ManyToManyField(User, related_name='student_subgroups', limit_choices_to=Q(user_type='Student'))

class Exam(models.Model):
    exam_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams', limit_choices_to=Q(user_type='Student'))
    completion_time = models.DurationField()
    exercises = models.ManyToManyField('Exercise', related_name='exams')

    @property
    def grade(self):
        return sum(exercise.score for exercise in self.exercises.all() if exercise.is_correct)

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
    is_correct = models.BooleanField(default=False)
    score = models.FloatField()

class RequestStateChoices(models.TextChoices):
    ON_HOLD = 'ON_HOLD', 'On hold'
    REJECTED = 'REJECTED', 'Rejected'
    ACCEPTED = 'ACCEPTED', 'Accepted'

class RequestGroup(models.Model):
    request_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_request_students', limit_choices_to=Q(user_type='Student'))
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_requests')
    teachers = models.ManyToManyField(User, related_name='group_request_teachers', limit_choices_to=Q(user_type='Teacher'))
    state = models.CharField(max_length=10, choices=RequestStateChoices.choices)

class RequestSubgroup(models.Model):
    request_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subgroup_request_students', limit_choices_to=Q(user_type='Student'))
    subgroup = models.ForeignKey(Subgroup, on_delete=models.CASCADE, related_name='subgroup_requests')
    teachers = models.ManyToManyField(User, related_name='subgroup_request_teachers', limit_choices_to=Q(user_type='Teacher'))
    state = models.CharField(max_length=10, choices=RequestStateChoices.choices)

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
