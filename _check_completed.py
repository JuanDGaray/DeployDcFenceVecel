import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dcfence.settings")
django.setup()

from collections import Counter
from django.db.models import Count
from customer.models import Project

log = open("_check_completed_out.txt", "w", encoding="utf-8")

def say(msg):
    log.write(str(msg) + "\n")
    log.flush()

status_counts = list(Project.objects.values("status").annotate(c=Count("id")).order_by("-c"))
say(f"status {status_counts}")

closed = Project.objects.filter(production_closed=True)
say(f"production_closed {closed.count()}")
years = Counter()
for p in closed.only("id", "status", "end_date", "production_closed_date", "updated_at", "project_name"):
    dt = p.production_closed_date or p.end_date
    years[getattr(dt, "year", None)] += 1
    if getattr(dt, "year", None) == 2026 or (p.updated_at and p.updated_at.year == 2026):
        say(f"2026-ish id={p.id} status={p.status} end={p.end_date} closed={p.production_closed_date} updated={p.updated_at} {p.project_name[:70]}")

say(f"closed years {sorted(years.items())}")

pending = Project.objects.filter(status="pending_payment")
say(f"pending_payment {pending.count()}")
for p in pending[:20]:
    say(f"pending id={p.id} end={p.end_date} closed={p.production_closed_date} {p.project_name[:70]}")

recent = Project.objects.filter(updated_at__year=2026).order_by("-updated_at")[:30]
say(f"updated 2026 {Project.objects.filter(updated_at__year=2026).count()}")
for p in recent:
    say(f"upd id={p.id} status={p.status} end={p.end_date} closed={p.production_closed_date} {p.project_name[:70]}")

log.close()
os._exit(0)
