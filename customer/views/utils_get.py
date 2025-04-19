
from django.contrib.auth.decorators import login_required
from customer.models import Project
from django.http import JsonResponse

@login_required
def get_projects(request):
    projects = list(Project.objects.all().order_by('project_name').values())
    projects_by_status = {}
    for project in projects:
        status = project['status']
        if status not in projects_by_status:
            projects_by_status[status] = []
        projects_by_status[status].append(project)
    print(projects_by_status)
    return JsonResponse(projects_by_status, safe=False)

