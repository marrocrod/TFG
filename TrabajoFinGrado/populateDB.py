import os
import django
from random import choice
from datetime import datetime

# Configura Django si este archivo está fuera del entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
django.setup()

from main.models import User, Exam, Exercise, Chat, Forum, Comment, ExerciseSet

def populate():
    # Grupos posibles basados en el modelo
    groups = [
        User.GroupChoices.GROUP_1,
        User.GroupChoices.GROUP_2,
        User.GroupChoices.GROUP_3,
        User.GroupChoices.GROUP_4
    ]

    # Datos únicos para profesores
    teacher_data = [
        {'first_name': 'Alice', 'last_name': 'Johnson', 'email': 'alice.johnson@example.com', 'degree': User.DegreeChoices.SOFTWARE_ENGINEERING, 'group': User.GroupChoices.GROUP_1},
        {'first_name': 'Bob', 'last_name': 'Smith', 'email': 'bob.smith@example.com', 'degree': User.DegreeChoices.HEALTH_ENGINEERING, 'group': User.GroupChoices.GROUP_2},
        {'first_name': 'Clara', 'last_name': 'Anderson', 'email': 'clara.anderson@example.com', 'degree': User.DegreeChoices.COMPUTER_ENGINEERING, 'group': User.GroupChoices.GROUP_3},
        {'first_name': 'David', 'last_name': 'White', 'email': 'david.white@example.com', 'degree': User.DegreeChoices.SOFTWARE_ENGINEERING, 'group': User.GroupChoices.GROUP_4},
        {'first_name': 'Eve', 'last_name': 'Davis', 'email': 'eve.davis@example.com', 'degree': User.DegreeChoices.HEALTH_ENGINEERING, 'group': User.GroupChoices.GROUP_1},
    ]

    # Crear profesores
    for teacher in teacher_data:
        username = f'{teacher["first_name"].lower()}.{teacher["last_name"].lower()}_teacher'

        new_teacher = User.objects.create_user(
            username=username,
            first_name=teacher['first_name'],
            last_name=teacher['last_name'],
            email=teacher['email'],
            password='password123',  # Contraseña común para todos
            user_type=User.UserTypeChoices.TEACHER,
            verification_status=User.VerificationStatus.APPROVED,  
            is_active=True,
            degree=teacher['degree'],
            group=teacher['group']  # Asignar grupo
        )
        new_teacher.save()
        print(f"Creado profesor: {new_teacher.username} ({new_teacher.email})")

    # Datos únicos para estudiantes
    student_data = [
        {'first_name': 'Adam', 'last_name': 'Brown', 'email': 'adam.brown@student.com', 'degree': User.DegreeChoices.SOFTWARE_ENGINEERING},
        {'first_name': 'Bella', 'last_name': 'Green', 'email': 'bella.green@student.com', 'degree': User.DegreeChoices.HEALTH_ENGINEERING},
        {'first_name': 'Charlie', 'last_name': 'Taylor', 'email': 'charlie.taylor@student.com', 'degree': User.DegreeChoices.COMPUTER_ENGINEERING},
        {'first_name': 'Diana', 'last_name': 'Moore', 'email': 'diana.moore@student.com', 'degree': User.DegreeChoices.SOFTWARE_ENGINEERING},
        {'first_name': 'Ethan', 'last_name': 'Wilson', 'email': 'ethan.wilson@student.com', 'degree': User.DegreeChoices.HEALTH_ENGINEERING},
        # Añadir más estudiantes según sea necesario
    ]

    # Crear estudiantes
    students = []
    for student in student_data:
        username = f'{student["first_name"].lower()}.{student["last_name"].lower()}_student'

        new_student = User.objects.create_user(
            username=username,
            first_name=student['first_name'],
            last_name=student['last_name'],
            email=student['email'],
            password='password123',  # Contraseña común para todos
            user_type=User.UserTypeChoices.STUDENT,
            is_active=True,
            degree=student['degree'],
            group=choice(groups)  # Asignar grupo aleatorio
        )
        new_student.save()
        students.append(new_student)
        print(f"Creado estudiante: {new_student.username} ({new_student.email})")

    # Crear exámenes y exercise sets para los estudiantes
    for student in students:
        exam_name = f"Examen {student.first_name} {student.last_name}"
        exam = Exam.objects.create(student=student, name=exam_name)

        # Crear un conjunto de ejercicios (ExerciseSet)
        exercise_set = ExerciseSet.objects.create(student=student, name=f"Set de ejercicios de {student.first_name}")

        # Crear ejercicios y asociarlos al conjunto de ejercicios y al examen
        for i in range(4):
            exercise = Exercise.objects.create(
                student=student,
                statement=f"Ejercicio {i + 1} para {student.first_name}",
                solution=f"Solución {i + 1}",
                difficulty='Easy',
                topic=1,
                exercise_set=exercise_set  # Asociar al conjunto de ejercicios
            )
            exam.exercises.add(exercise)

        exam.save()
        print(f"Creado examen para {student.username}: {exam.name}")

    # Crear chats para los estudiantes
    for student in students:
        chat = Chat.objects.create(
            student=student,
            url=f"https://chat/{student.username}",
            conversation="[]"
        )
        chat.add_message("user", f"Hola, soy {student.first_name}. ¿Cómo estás?")
        chat.add_message("assistant", "¡Hola! Estoy aquí para ayudarte.")
        print(f"Creado chat para {student.username}")

    # Crear foros y comentarios
    for i, teacher in enumerate(User.objects.filter(user_type=User.UserTypeChoices.TEACHER)):
        forum = Forum.objects.create(
            title=f"Debate {i + 1} creado por {teacher.first_name}",
            description=f"Descripción del foro {i + 1}",
            created_by=teacher,
            image=None
        )
        print(f"Foro creado: {forum.title}")

        # Añadir comentarios de los estudiantes
        for student in students:
            comment = Comment.objects.create(
                forum=forum,
                user=student,
                content=f"Comentario de {student.first_name} en el foro {forum.title}"
            )
            print(f"Comentario añadido por {student.username} en {forum.title}")

if __name__ == '__main__':
    print("Iniciando la creación de usuarios, exámenes, chats y foros...")
    populate()
    print("Población completada.")
