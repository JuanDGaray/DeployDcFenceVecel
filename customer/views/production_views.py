from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Customer, Project, User, TaskProject, RealCostProject
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
    RealCost = RealCostProject.objects.filter(project=project)
    RealCostByItems = None
    if len(RealCost) > 0:
        RealCostItems = RealCost.get()
        RealCostByItems = RealCostItems

    proposal = project.get_approved_proposal()
    budget = proposal.budget
    costData = {}
    progress = 0
    last_index = None
    for elemet in budget.dataPreview:
        if len(elemet) >= 2:
            costData[elemet[0]] = {'total':elemet[1], 'content':[]}
            last_index = budget.dataPreview.index(elemet)
        else:
            costData[budget.dataPreview[last_index][0]]['content'].append(elemet[0])

    if taskGantt.exists():
        print(taskGantt.first().gantt_data)
        gantt_data = taskGantt.first().gantt_data
        progress = calculate_project_progress(gantt_data)
    else:
        gantt_data = []

    return render(request, 'detail_production_project.html', {
        'project': project,
        'today': timezone.now().date(),
        'ganttData': json.dumps(gantt_data),
        'budget': budget,
        'costData': json.dumps(costData),
        'date': timezone.now().date(),
        'data' : json.dumps(extract_data_budget(budget)),
        'progress': round(progress*100),
        'taskGantt':taskGantt,
        'realCostItems': json.dumps(RealCostByItems.items)
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

dictItems = {}

@login_required
def save_real_cost_by_items(request, project_id):
    try:
        project = get_object_or_404(Project, pk=project_id)
        if request.method == 'POST':
            costData = request.body
            costData = json.loads(costData)
            realCostData, created = RealCostProject.objects.get_or_create(project=project)
            
            if len(realCostData.items)>0:
                dictItems = realCostData.items
                print('papa', dictItems)
            else:
                dictItems = {}
            concept = costData['concept']
            description = costData['description']
            costValue = costData['costValue']
            item = costData['item']
            if item not in dictItems:
                dictItems[item] = {'subItems':{}, 'total':0}
                dictItems[item]['subItems'][concept] = {}
                dictItems[item]['subItems'][concept][description]=float(costValue)
            elif concept not in dictItems[item]['subItems']:
                dictItems[item]['subItems'][concept] = {}
                dictItems[item]['subItems'][concept][description]=float(costValue)
            else:
                dictItems[item]['subItems'][concept][description]=float(costValue)
                
            dictItems[item]['total'] = sum(
                value
                for description in dictItems[item]['subItems'].values()
                for value in description.values()
            )
            print(dictItems)
            realCostData.items = dictItems
            realCostData.save()
        
            
            return JsonResponse({'status': 'success', 'message': 'Project dates updated successfully'}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

def calculate_project_progress(tasks):
    total_progress = 0
    total_duration = 0
    
    for task in tasks:
        progress = task.get('progress', 0)
        duration = task.get('duration', 0)
        
        # Asegurarse de que la duración no sea 0 para evitar la división por 0
        if duration > 0:
            weighted_progress = progress * duration
            total_progress += weighted_progress
            total_duration += duration
    

    if total_duration == 0:
        return 0
    
    return total_progress / total_duration


