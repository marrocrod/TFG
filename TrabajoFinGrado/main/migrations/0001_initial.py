# Generated by Django 4.2.7 on 2024-08-19 20:29

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('degree', models.CharField(choices=[('Software Engineering', 'Software Engineering'), ('Health Engineering', 'Health Engineering'), ('Computer Engineering', 'Computer Engineering')], max_length=100)),
                ('user_type', models.CharField(choices=[('Teacher', 'Teacher'), ('Student', 'Student')], max_length=10)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='users_in_auth_groups', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='users_with_permissions', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('course_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups_in_course', to='main.course')),
                ('students', models.ManyToManyField(limit_choices_to=models.Q(('user_type', 'Student')), related_name='student_groups', to=settings.AUTH_USER_MODEL)),
                ('teachers', models.ManyToManyField(limit_choices_to=models.Q(('user_type', 'Teacher')), related_name='teaching_groups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Subgroup',
            fields=[
                ('subgroup_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subgroups', to='main.group')),
                ('students', models.ManyToManyField(limit_choices_to=models.Q(('user_type', 'Student')), related_name='student_subgroups', to=settings.AUTH_USER_MODEL)),
                ('teachers', models.ManyToManyField(limit_choices_to=models.Q(('user_type', 'Teacher')), related_name='teaching_subgroups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RequestSubgroup',
            fields=[
                ('request_id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.CharField(choices=[('ON_HOLD', 'On hold'), ('REJECTED', 'Rejected'), ('ACCEPTED', 'Accepted')], max_length=10)),
                ('student', models.ForeignKey(limit_choices_to=models.Q(('user_type', 'Student')), on_delete=django.db.models.deletion.CASCADE, related_name='subgroup_request_students', to=settings.AUTH_USER_MODEL)),
                ('subgroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subgroup_requests', to='main.subgroup')),
                ('teachers', models.ManyToManyField(limit_choices_to=models.Q(('user_type', 'Teacher')), related_name='subgroup_request_teachers', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RequestGroup',
            fields=[
                ('request_id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.CharField(choices=[('ON_HOLD', 'On hold'), ('REJECTED', 'Rejected'), ('ACCEPTED', 'Accepted')], max_length=10)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_requests', to='main.group')),
                ('student', models.ForeignKey(limit_choices_to=models.Q(('user_type', 'Student')), on_delete=django.db.models.deletion.CASCADE, related_name='group_request_students', to=settings.AUTH_USER_MODEL)),
                ('teachers', models.ManyToManyField(limit_choices_to=models.Q(('user_type', 'Teacher')), related_name='group_request_teachers', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('exercise_id', models.AutoField(primary_key=True, serialize=False)),
                ('statement', models.TextField()),
                ('solution', models.TextField()),
                ('is_correct', models.BooleanField(default=False)),
                ('score', models.FloatField()),
                ('student', models.ForeignKey(limit_choices_to=models.Q(('user_type', 'Student')), on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('exam_id', models.AutoField(primary_key=True, serialize=False)),
                ('completion_time', models.DurationField()),
                ('exercises', models.ManyToManyField(related_name='exams', to='main.exercise')),
                ('student', models.ForeignKey(limit_choices_to=models.Q(('user_type', 'Student')), on_delete=django.db.models.deletion.CASCADE, related_name='exams', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='groups',
            field=models.ManyToManyField(related_name='courses_in', to='main.group'),
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('chat_id', models.AutoField(primary_key=True, serialize=False)),
                ('url', models.URLField()),
                ('student', models.ForeignKey(limit_choices_to=models.Q(('user_type', 'Student')), on_delete=django.db.models.deletion.CASCADE, related_name='chats', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
