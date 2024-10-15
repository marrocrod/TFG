# main/management/commands/notify_events.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from main.models import Event

class Command(BaseCommand):
    help = 'Envia notificaciones por correo 24 horas antes de los eventos programados'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        next_24_hours = now + timezone.timedelta(hours=24)
        
        # Buscar eventos que ocurran dentro de las próximas 24 horas
        events = Event.objects.filter(start_time__gte=now, start_time__lte=next_24_hours)

        for event in events:
            user = event.user
            # Enviar el correo de notificación
            send_mail(
                'Recordatorio: Evento en 24 horas',
                f'Hola {user.username}, tienes el evento "{event.title}" en 24 horas.',
                'saympl3xfp@gmail.com',  # Reemplazar con tu correo
                [user.email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Se ha enviado el correo a {user.email} para el evento "{event.title}"'))
