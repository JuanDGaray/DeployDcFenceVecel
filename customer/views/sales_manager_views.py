from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from ..models import Project
from .projects_views import log_project_history, user_is_admin, manager_needs_reassign

User = get_user_model()


@login_required
def assign_sales_manager(request, project_id, manager_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    if not user_is_admin(request.user):
        return JsonResponse({
            'status': 'error',
            'message': 'Only administrators can assign the sales manager.',
        }, status=403)

    try:
        project = get_object_or_404(Project, id=project_id)
        manager = get_object_or_404(User, id=manager_id, is_active=True)

        if not manager_needs_reassign(project.sales_advisor):
            return JsonResponse({
                'status': 'error',
                'message': 'Sales manager is already assigned and active.',
            }, status=400)

        project.sales_advisor = manager
        project.save()

        log_project_history(
            request,
            project,
            'UPDATE',
            f'Sales manager assigned to {manager.get_full_name()}',
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Sales manager {manager.get_full_name()} assigned successfully',
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error assigning sales manager: {str(e)}',
        }, status=400)
