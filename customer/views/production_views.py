from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Customer, Project, User, TaskProject
from ..form import CustomerForm 
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json
from .projects_views import extract_data_budget

@login_required
def production(request):
    # Retrieves the list of all customers and paginates it
    Project_list = Project.objects.filter(status="in_production")
    paginator = Paginator(Project_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sellers = User.objects.all()
    customers = Customer.objects.all()
    current_user = request.user  
    if request.method == 'GET':

        # Renders the customer list view with pagination
        return render(request, 'productionIndex.html', {
            'projects': page_obj,
            'total_projects': Project_list.count(),
            'view': 'production',
            'current_user': current_user, 
            'customers': customers,
            'sellers': sellers   
        })

@login_required
def production_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    taskGantt = TaskProject.objects.filter(project=project)
    proposal = project.get_approved_proposal()
    budget = proposal.budget
    
    if taskGantt.exists():
        print(taskGantt.first().gantt_data)
        gantt_data = taskGantt.first().gantt_data
    else:
        gantt_data = []

    return render(request, 'detail_production_project.html', {
        'project': project,
        'today': timezone.now().date(),
        'ganttData': json.dumps(gantt_data),
        'budget': budget,
        'date': timezone.now().date(),
        'data' : json.dumps(extract_data_budget(budget))
    })
    
    
@login_required
def setDateInProduction(request, project_id, start_date, end_date):
    try:
        project = get_object_or_404(Project, pk=project_id)
        project.start_date = start_date
        project.end_date = end_date
        project.save()
        return JsonResponse({'status': 'success', 'message': 'Project dates updated successfully'}, status=200)

    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': f'Validation error: {str(e)}'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)
    
@login_required     
def save_gantt_data(request, project_id):
    try:
        project = get_object_or_404(Project, pk=project_id)
        if request.method == 'POST':
            gantt_data = request.body
            gantt_data = json.loads(gantt_data)
            task_project, created = TaskProject.objects.get_or_create(project=project)
            task_project.gantt_data = gantt_data['gantt_data']['data']
            task_project.save()
            return JsonResponse({'status': 'success', 'message': 'Project dates updated successfully'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    
    except KeyError as e:
        return JsonResponse({'status': 'error', 'message': f'Missing key: {str(e)}'}, status=400)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)
