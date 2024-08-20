from django.urls import path
from .views import student_profile

urlpatterns = [
    path('profile/', student_profile, name='profile'),
]
