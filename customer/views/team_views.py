from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.http import JsonResponse
from django.contrib.auth import get_user_model

def get_active_users():
    User = get_user_model()
    sessions = Session.objects.filter(expire_date__gte=now())  # Sesiones no expiradas
    user_ids = []  # IDs de usuarios con sesiones activas

    for session in sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')  # Extrae el ID del usuario
        if user_id:
            user_ids.append(user_id)

    return User.objects.filter(id__in=user_ids)

def active_users_view(request):
    users = get_active_users()
    user_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
    return JsonResponse({'active_users': user_data})
