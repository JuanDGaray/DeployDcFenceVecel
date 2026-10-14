from datetime import datetime, timedelta

from django.contrib.sessions.models import Session
from django.utils import timezone

# Touch the session at most this often, and treat the user as online
# only if that stamp is still inside the window.
ACTIVITY_TOUCH = timedelta(seconds=60)
ONLINE_WINDOW = timedelta(minutes=5)


def touch_last_activity(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return

    now = timezone.now()
    previous = _parse_stamp(request.session.get("last_activity"))
    if previous is not None and now - previous < ACTIVITY_TOUCH:
        return

    request.session["last_activity"] = now.isoformat()


def get_online_user_ids():
    cutoff = timezone.now() - ONLINE_WINDOW
    user_ids = set()
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        data = session.get_decoded()
        user_id = data.get("_auth_user_id")
        seen = _parse_stamp(data.get("last_activity"))
        if not user_id or seen is None or seen < cutoff:
            continue
        try:
            user_ids.add(int(user_id))
        except (TypeError, ValueError):
            continue
    return user_ids


def _parse_stamp(raw):
    if not raw:
        return None
    try:
        seen = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return None
    if timezone.is_naive(seen):
        seen = timezone.make_aware(seen, timezone.get_current_timezone())
    return seen
