from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import (
    BugAttachment,
    BugChecklistItem,
    BugComment,
    BugHistory,
    BugReport,
    Notification,
)

DEFAULT_CHECKLIST = [
    "Reproduce the error",
    "Identify the cause",
    "Implement a fix",
    "Test the fix",
    "Confirm the error is gone",
    "Close the report",
]

IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
MAX_SCREENSHOT_BYTES = 8 * 1024 * 1024


def user_can_manage_bugs(user):
    if not user.is_authenticated:
        return False
    return (
        user.is_superuser
        or user.is_staff
        or user.groups.filter(name__in=["DEVELOPER", "ADMIN"]).exists()
    )


def _developers():
    developers = User.objects.filter(groups__name="DEVELOPER", is_active=True).distinct()
    if developers.exists():
        return developers
    return User.objects.filter(is_superuser=True, is_active=True)


def _can_view(user, bug):
    return user_can_manage_bugs(user) or bug.reporter_id == user.id


def _log(bug, user, action, description):
    BugHistory.objects.create(bug=bug, user=user, action=action, description=description)


def _notify(bug, sender, recipients, notification_type, message):
    seen = set()
    for recipient in recipients:
        if recipient is None or recipient.id in seen:
            continue
        if sender is not None and recipient.id == sender.id:
            continue
        seen.add(recipient.id)
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            bug=bug,
            message=message,
        )


def _clean_page_url(raw):
    raw = (raw or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc:
        path = parsed.path or "/"
        candidate = f"{path}?{parsed.query}" if parsed.query else path
    else:
        candidate = raw.split("#", 1)[0]
    if not candidate.startswith("/") or candidate.startswith("//"):
        return ""
    return candidate[:500]


def _bug_message(bug, headline):
    created = timezone.localtime(bug.created_at) if bug.created_at else timezone.localtime()
    reporter = bug.reporter.get_full_name() or bug.reporter.username
    page = f"<br>Page: {bug.page_url}" if bug.page_url else ""
    return (
        f"<strong>{headline}</strong><br>"
        f"{bug.title}<br>"
        f"Urgency: {bug.get_urgency_display()}<br>"
        f"Reported by {reporter}"
        f"{page}<br>"
        f"{created.strftime('%b %d, %Y %H:%M')}"
    )


def _save_screenshot(bug, uploaded, user):
    if not uploaded:
        return None
    content_type = (getattr(uploaded, "content_type", "") or "").lower()
    if content_type not in IMAGE_TYPES:
        return "Attach a PNG, JPG, WEBP, or GIF image."
    if uploaded.size > MAX_SCREENSHOT_BYTES:
        return "The screenshot must be 8 MB or smaller."
    uploaded.seek(0)
    BugAttachment.objects.create(
        bug=bug,
        uploaded_by=user,
        data=uploaded.read(),
        content_type=content_type,
        original_name=(uploaded.name or "screenshot.png")[:200],
    )
    return None


@login_required
def bug_list(request):
    can_manage = user_can_manage_bugs(request.user)
    bugs = BugReport.objects.select_related("reporter", "assignee")
    if not can_manage:
        bugs = bugs.filter(reporter=request.user)

    status = request.GET.get("status") or ""
    urgency = request.GET.get("urgency") or ""
    assignee = request.GET.get("assignee") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""
    query = (request.GET.get("q") or "").strip()

    if can_manage:
        if status in dict(BugReport.STATUS_CHOICES):
            bugs = bugs.filter(status=status)
        if urgency in dict(BugReport.URGENCY_CHOICES):
            bugs = bugs.filter(urgency=urgency)
        if assignee.isdigit():
            bugs = bugs.filter(assignee_id=int(assignee))
        if date_from:
            bugs = bugs.filter(created_at__date__gte=date_from)
        if date_to:
            bugs = bugs.filter(created_at__date__lte=date_to)
        if query:
            bugs = bugs.filter(
                Q(title__icontains=query) | Q(description__icontains=query) | Q(page_url__icontains=query)
            )

    stats = {}
    if can_manage:
        all_bugs = BugReport.objects.all()
        stats = {
            "total": all_bugs.count(),
            "pending": all_bugs.filter(status__in=["new", "pending", "reopened"]).count(),
            "in_progress": all_bugs.filter(status__in=["in_progress", "in_review"]).count(),
            "resolved": all_bugs.filter(status__in=["resolved", "closed"]).count(),
            "urgent": all_bugs.filter(urgency__in=["critical", "high"]).exclude(status__in=["resolved", "closed"]).count(),
        }

    return render(request, "bugs/list.html", {
        "view": "bugs",
        "bugs": bugs,
        "can_manage": can_manage,
        "stats": stats,
        "developers": _developers() if can_manage else [],
        "status_choices": BugReport.STATUS_CHOICES,
        "urgency_choices": BugReport.URGENCY_CHOICES,
        "filters": {
            "status": status,
            "urgency": urgency,
            "assignee": assignee,
            "date_from": date_from,
            "date_to": date_to,
            "q": query,
        },
    })


@login_required
@require_POST
def bug_create(request):
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    page_url = _clean_page_url(request.POST.get("page_url") or request.META.get("HTTP_REFERER"))
    urgency = request.POST.get("urgency") or BugReport.URGENCY_MEDIUM
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not title or not description:
        message = "Title and description are required."
        if is_ajax:
            return JsonResponse({"error": message}, status=400)
        return redirect("/bugs/")
    if urgency not in dict(BugReport.URGENCY_CHOICES):
        urgency = BugReport.URGENCY_MEDIUM

    bug = BugReport.objects.create(
        title=title,
        description=description,
        page_url=page_url,
        urgency=urgency,
        status=BugReport.STATUS_NEW,
        reporter=request.user,
    )
    screenshot_error = _save_screenshot(bug, request.FILES.get("screenshot"), request.user)
    if screenshot_error:
        bug.delete()
        if is_ajax:
            return JsonResponse({"error": screenshot_error}, status=400)
        return redirect("/bugs/")

    for index, label in enumerate(DEFAULT_CHECKLIST):
        BugChecklistItem.objects.create(bug=bug, title=label, position=index)
    where = f" on {bug.page_url}" if bug.page_url else ""
    _log(bug, request.user, "created", f"Report created with urgency {bug.get_urgency_display()}{where}.")
    _notify(
        bug,
        request.user,
        _developers(),
        "bug_report",
        _bug_message(bug, "New bug report"),
    )
    if is_ajax:
        return JsonResponse({"success": True, "id": bug.id, "url": f"/bugs/{bug.id}/"})
    return redirect(f"/bugs/{bug.id}/?created=1")


@login_required
def bug_attachment(request, attachment_id):
    attachment = get_object_or_404(BugAttachment.objects.select_related("bug"), id=attachment_id)
    if not _can_view(request.user, attachment.bug):
        return HttpResponseForbidden("You cannot open this screenshot.")
    if not attachment.data:
        return HttpResponse(status=404)
    response = HttpResponse(bytes(attachment.data), content_type=attachment.content_type or "image/png")
    response["Content-Disposition"] = "inline"
    response["Cache-Control"] = "private, max-age=3600"
    return response


@login_required
def bug_detail(request, bug_id):
    bug = get_object_or_404(
        BugReport.objects.select_related("reporter", "assignee"),
        id=bug_id,
    )
    if not _can_view(request.user, bug):
        return render(request, "bugs/forbidden.html", status=403)
    can_manage = user_can_manage_bugs(request.user)
    items = list(bug.checklist_items.all())
    done = sum(1 for item in items if item.is_done)
    return render(request, "bugs/detail.html", {
        "view": "bugs",
        "bug": bug,
        "can_manage": can_manage,
        "attachments": bug.attachments.all(),
        "comments": bug.comments.select_related("author"),
        "history": bug.history.select_related("user"),
        "checklist": items,
        "checklist_done": done,
        "checklist_total": len(items),
        "developers": _developers() if can_manage else [],
        "status_choices": BugReport.STATUS_CHOICES,
        "created_now": request.GET.get("created") == "1",
    })


@login_required
@require_POST
def bug_update_status(request, bug_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if not user_can_manage_bugs(request.user):
        return HttpResponseForbidden("Only developers can change the status.")
    new_status = request.POST.get("status")
    if new_status not in dict(BugReport.STATUS_CHOICES):
        return redirect(f"/bugs/{bug.id}/")
    if new_status != bug.status:
        previous = bug.get_status_display()
        bug.status = new_status
        bug.save(update_fields=["status", "updated_at"])
        _log(bug, request.user, "status", f"Status changed from {previous} to {bug.get_status_display()}.")
        recipients = [bug.reporter, bug.assignee]
        _notify(
            bug,
            request.user,
            recipients,
            "bug_status",
            f"<strong>Status: {bug.get_status_display()}</strong><br>{bug.title}<br>Urgency: {bug.get_urgency_display()}",
        )
    return redirect(f"/bugs/{bug.id}/")


@login_required
@require_POST
def bug_assign(request, bug_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if not user_can_manage_bugs(request.user):
        return HttpResponseForbidden("Only developers can assign a report.")
    assignee_id = request.POST.get("assignee_id") or ""
    assignee = None
    if assignee_id.isdigit():
        assignee = _developers().filter(id=int(assignee_id)).first()
        if assignee is None:
            return redirect(f"/bugs/{bug.id}/")
    if bug.assignee_id != (assignee.id if assignee else None):
        bug.assignee = assignee
        bug.save(update_fields=["assignee", "updated_at"])
        name = assignee.get_full_name() if assignee else "nobody"
        _log(bug, request.user, "assign", f"Assigned to {name}.")
        if assignee:
            _notify(
                bug,
                request.user,
                [assignee],
                "bug_assigned",
                _bug_message(bug, "Bug assigned to you"),
            )
    return redirect(f"/bugs/{bug.id}/")


@login_required
@require_POST
def bug_comment(request, bug_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if not _can_view(request.user, bug):
        return HttpResponseForbidden("You cannot comment on this report.")
    body = (request.POST.get("body") or "").strip()
    if body:
        BugComment.objects.create(bug=bug, author=request.user, body=body)
        bug.save(update_fields=["updated_at"])
        _log(bug, request.user, "comment", body[:500])
        recipients = [bug.reporter, bug.assignee]
        if not user_can_manage_bugs(request.user):
            recipients.extend(list(_developers()))
        _notify(
            bug,
            request.user,
            recipients,
            "bug_comment",
            f"<strong>New comment</strong><br>{bug.title}<br>{body[:240]}",
        )
    return redirect(f"/bugs/{bug.id}/")


@login_required
@require_POST
def bug_checklist_add(request, bug_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if not user_can_manage_bugs(request.user):
        return JsonResponse({"error": "Only developers can edit the checklist."}, status=403)
    title = (request.POST.get("title") or "").strip()
    if not title:
        return JsonResponse({"error": "Title is required."}, status=400)
    last = bug.checklist_items.order_by("-position").first()
    item = BugChecklistItem.objects.create(
        bug=bug,
        title=title,
        position=(last.position + 1) if last else 0,
    )
    bug.save(update_fields=["updated_at"])
    _log(bug, request.user, "checklist", f'Added checklist item "{item.title}".')
    return JsonResponse({"success": True, "id": item.id, "title": item.title})


@login_required
@require_POST
def bug_checklist_update(request, bug_id, item_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if not user_can_manage_bugs(request.user):
        return JsonResponse({"error": "Only developers can edit the checklist."}, status=403)
    item = get_object_or_404(BugChecklistItem, id=item_id, bug=bug)
    changed = False
    if "is_done" in request.POST:
        is_done = request.POST.get("is_done") in ("1", "true", "on")
        if item.is_done != is_done:
            item.is_done = is_done
            changed = True
    if "title" in request.POST:
        title = (request.POST.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "Title is required."}, status=400)
        if item.title != title:
            item.title = title
            changed = True
    if changed:
        item.save()
        bug.save(update_fields=["updated_at"])
        state = "done" if item.is_done else "open"
        _log(bug, request.user, "checklist", f'Checklist item "{item.title}" is {state}.')
    done = bug.checklist_items.filter(is_done=True).count()
    total = bug.checklist_items.count()
    return JsonResponse({"success": True, "is_done": item.is_done, "done": done, "total": total})


@login_required
@require_POST
def bug_checklist_delete(request, bug_id, item_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if not user_can_manage_bugs(request.user):
        return JsonResponse({"error": "Only developers can edit the checklist."}, status=403)
    item = get_object_or_404(BugChecklistItem, id=item_id, bug=bug)
    title = item.title
    item.delete()
    bug.save(update_fields=["updated_at"])
    _log(bug, request.user, "checklist", f'Removed checklist item "{title}".')
    done = bug.checklist_items.filter(is_done=True).count()
    total = bug.checklist_items.count()
    return JsonResponse({"success": True, "done": done, "total": total})
