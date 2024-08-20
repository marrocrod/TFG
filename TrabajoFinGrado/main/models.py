from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)

    class DegreeChoices(models.TextChoices):
        SOFTWARE_ENGINEERING = 'Software Engineering'
        HEALTH_ENGINEERING = 'Health Engineering'
        COMPUTER_ENGINEERING = 'Computer Engineering'
    
    degree = models.CharField(max_length=100, choices=DegreeChoices.choices)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='users',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    @property
    def is_teacher(self):
        return hasattr(self, 'teacher_profile')

    @property
    def is_student(self):
        return hasattr(self, 'student_profile')

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.AutoField(primary_key=True)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.AutoField(primary_key=True)

class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    groups = models.ManyToManyField('Group', related_name='courses_in')

class Group(models.Model):
    group_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups_in_course')
    teachers = models.ManyToManyField(Teacher, related_name='groups')
    students = models.ManyToManyField(Student, related_name='groups')

class Subgroup(models.Model):
    subgroup_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='subgroups')
    teachers = models.ManyToManyField(Teacher, related_name='subgroups')
    students = models.ManyToManyField(Student, related_name='subgroups')

class Exam(models.Model):
    exam_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exams')
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
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exercises')
    statement = models.TextField()
    solution = models.TextField()
    is_correct = models.BooleanField(default=False)
    score = models.FloatField()

class RequestGroup(models.Model):
    request_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='group_requests')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_requests')
    teachers = models.ManyToManyField(Teacher, related_name='group_requests')
    state = models.CharField(max_length=10, choices=[
        ('ON_HOLD', 'On hold'),
        ('REJECTED', 'Rejected'),
        ('ACCEPTED', 'Accepted'),
    ])

class RequestSubgroup(models.Model):
    request_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subgroup_requests')
    subgroup = models.ForeignKey(Subgroup, on_delete=models.CASCADE, related_name='subgroup_requests')
    teachers = models.ManyToManyField(Teacher, related_name='subgroup_requests')
    state = models.CharField(max_length=10, choices=[
        ('ON_HOLD', 'On hold'),
        ('REJECTED', 'Rejected'),
        ('ACCEPTED', 'Accepted'),
    ])

class Chat(models.Model):
    chat_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='chats')
    url = models.URLField()

    def __str__(self):
        return f"Chat with {self.student.user.username}"
