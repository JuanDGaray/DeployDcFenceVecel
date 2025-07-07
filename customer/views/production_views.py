from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Customer, Project, User, TaskProject, RealCostProject, Notification, ProductionChangeLog
from ..form import CustomerForm 
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json
from .projects_views import extract_data_budget, log_project_history
from datetime import datetime
from django.contrib.auth.models import Group
from ..utils import create_manager_assignment_notification
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..models import ProductionFundingRequest
from django.contrib.auth import get_user_model
import copy
User = get_user_model()

@login_required
def production(request):
    # Retrieves the list of all customers and paginates it
    Project_list = Project.objects.filter(status="in_production").only('id', 'project_name', 'status', 'customer', 'sales_advisor', 'accounting_manager', 'start_date', 'end_date')
    paginator = Paginator(Project_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sellers = User.objects.only('id', 'username', 'first_name', 'last_name')
    customers = Customer.objects.only('id', 'company_name', 'first_name', 'last_name', 'customer_type')
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
    if type(project_id) == str:
        project_id = int(project_id)
    project = get_object_or_404(Project, pk=project_id)
    if project.accounting_manager == None or project.sales_advisor == None or project.project_manager == None or project.start_date == None or project.end_date == None:
        groups = Group.objects.prefetch_related("user_set").all()
        admin_users = []
        production_users = []
        for group in groups:
            if group.name == "ADMIN":
                admin_users = [{"name": user.first_name + " " + user.last_name, "email": user.email, "id":  user.id} for user in group.user_set.all()]
            elif group.name == "PRODUCTION":
                production_users = [{"name": user.first_name + " " + user.last_name, "email": user.email, "id":  user.id} for user in group.user_set.all()]
        productionUsers = {'Admins': admin_users, 'Managers':production_users}

        return render(request, 'detail_production_project.html', {
            'project': project,
            'productionUsers': productionUsers,
        })

    taskGantt = TaskProject.objects.filter(project=project)
    RealCost = RealCostProject.objects.filter(project=project)

    RealCostByItems = None
    if RealCost.exists():
        RealCostItems = RealCost.get()
        if RealCostItems: 
            RealCostByItems = json.dumps(RealCostItems.items)

    print(RealCostByItems, 'RealCostByItems')
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
        # Si gantt_data es un diccionario con 'data' y 'links', usar solo 'data' para el progreso
        if isinstance(gantt_data, dict) and 'data' in gantt_data:
            progress = calculate_project_progress(gantt_data['data'])
        else:
            # Para compatibilidad con datos antiguos
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
        'realCostItems': RealCostByItems,
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
            # Guardar tanto las tareas como los links
            gantt_data_to_save = {
                'data': gantt_data['gantt_data']['data'],
                'links': gantt_data['gantt_data']['links'] if 'links' in gantt_data['gantt_data'] else []
            }
            task_project.gantt_data = gantt_data_to_save
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
    def sum_all_cost_values(obj):
        total = 0
        if isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, dict):
                    if 'costValue' in v:
                        try:
                            total += float(v['costValue'])
                        except (ValueError, TypeError):
                            pass
                    else:
                        total += sum_all_cost_values(v)
                elif isinstance(v, (int, float)):
                    total += v
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                total += sum_all_cost_values(item)
        return total

    try:
        project = get_object_or_404(Project, pk=project_id)
        if request.method == 'POST':
            costData = request.body
            costData = json.loads(costData)
            realCostData, created = RealCostProject.objects.get_or_create(project=project)
            
            if len(realCostData.items) > 0:
                dictItems = realCostData.items
            else:
                dictItems = {}

            # Copia profunda del estado anterior
            data_before = copy.deepcopy(dictItems)

            concept = costData['concept']
            description = costData['description']
            costValue = costData['costValue']
            item = costData['item']
            url_evidence = costData.get('evidence_url', None)
            if item not in dictItems:
                dictItems[item] = {'subItems':{}, 'total':0}
                dictItems[item]['subItems'][concept] = {}
                dictItems[item]['subItems'][concept][description] = {'costValue':float(costValue)}
            elif concept not in dictItems[item]['subItems']:
                dictItems[item]['subItems'][concept] = {}
                dictItems[item]['subItems'][concept][description] = {'costValue':float(costValue)}
            else:
                dictItems[item]['subItems'][concept][description] = {'costValue':float(costValue)}

            if url_evidence:
                dictItems[item]['subItems'][concept][description]['evidence_url'] = url_evidence
            else:
                dictItems[item]['subItems'][concept][description]['evidence_url'] = None

            dictItems[item]['total'] = sum_all_cost_values(dictItems[item]['subItems'])
            realCostData.items = dictItems
            realCostData.save()

            # Guardar en el historial
            ProductionChangeLog.objects.create(
                project=project,
                user=request.user,
                action="update_real_cost",
                description=f"Actualización de costos reales para el item {item}",
                data_before=data_before,
                data_after=dictItems
            )
        
            return JsonResponse({'status': 'success', 'message': 'Project dates updated successfully'}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

def calculate_project_progress(tasks):
    total_progress = 0
    total_duration = 0

    for task in tasks:
        progress = task.get('progress', 0) or 0
        duration = task.get('duration', 0) or 0

        # Si duration es 0 o no existe, intenta calcularlo a partir de las fechas
        if (not duration or duration == 0) and task.get('start_date') and task.get('end_date'):
            try:
                start = task['start_date']
                end = task['end_date']
                if isinstance(start, str):
                    try:
                        start = datetime.fromisoformat(start)
                    except ValueError:
                        start = datetime.strptime(start[:10], '%Y-%m-%d')
                if isinstance(end, str):
                    try:
                        end = datetime.fromisoformat(end)
                    except ValueError:
                        end = datetime.strptime(end[:10], '%Y-%m-%d')
                duration = (end - start).days or 1  # Al menos 1 día
            except Exception as e:
                duration = 0

        try:
            progress = float(progress)
        except (TypeError, ValueError):
            progress = 0
        try:
            duration = float(duration)
        except (TypeError, ValueError):
            duration = 0

        if duration > 0:
            weighted_progress = progress * duration
            total_progress += weighted_progress
            total_duration += duration

    if total_duration == 0:
        return 0

    return total_progress / total_duration

@login_required
def update_project_production(request, project_id):
    if request.method == 'POST':
        try:
            if request.user != project.project_manager and not request.user.is_superuser and request.user != project.accounting_manager and request.user != project.sales_advisor:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You are not authorized to update this project'
                }, status=403)
            project = get_object_or_404(Project, pk=project_id)
            
            # Get form data
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            accounting_manager_id = request.POST.get('accounting_manager_id')
            project_manager_id = request.POST.get('project_manager_id')
            
            # Validate required fields
            errors = []
            
            if not start_date:
                errors.append('Start date is required')
            if not end_date:
                errors.append('End date is required')
            
            # Only validate managers if they are not already assigned
            if not project.accounting_manager and not accounting_manager_id:
                errors.append('Accounting manager is required')
            if not project.project_manager and not project_manager_id:
                errors.append('Project manager is required')
            
            if errors:
                return JsonResponse({
                    'status': 'error',
                    'message': '; '.join(errors)
                }, status=400)
            
            # Validate date logic
            if start_date and end_date:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                if end_date_obj <= start_date_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'End date must be after start date'
                    }, status=400)
            
            # Update project fields
            if start_date:
                project.start_date = start_date
            if end_date:
                project.end_date = end_date
            if accounting_manager_id:
                accounting_manager = get_object_or_404(User, id=accounting_manager_id)
                project.accounting_manager = accounting_manager
                create_manager_assignment_notification(project, accounting_manager, 'accounting', request.user)
            if project_manager_id:
                project_manager = get_object_or_404(User, id=project_manager_id)
                project.project_manager = project_manager
                create_manager_assignment_notification(project, project_manager, 'production', request.user)
            # Save the project
            project.save()

            # Log the update
            log_project_history(request, project, 'UPDATE', 'Project production settings updated')
            
            return JsonResponse({
                'status': 'success',
                'message': 'Project updated successfully'
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid manager ID provided'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error updating project: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)

@csrf_exempt
@require_POST
@login_required
def request_cost_by_pm(request, project_id):
    project = Project.objects.get(id=project_id)
    if request.user == project.project_manager:
        if not project.production_funding_request:
            # Obtener el tipo de cost request del request
            data = json.loads(request.body)
            cost_request_type = data.get('cost_request_type')
            
            funding_request = ProductionFundingRequest.objects.create(
                project=project, 
                requested_by=request.user,
                cost_request_type=cost_request_type
            )
            project.production_funding_request = funding_request
            project.save()
            # Notifica al accounting_manager
            Notification.objects.create(
                recipient=project.accounting_manager,
                sender=request.user,
                notification_type='project_update',
                project=project,
                message=f"{request.user.first_name} {request.user.last_name} request a cost request ({cost_request_type}) for the project {project.project_name}."
            )
            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({'status': 'already_requested'})
    return JsonResponse({'status': 'forbidden'}, status=403)

@csrf_exempt
@require_POST
@login_required
def assign_cost_by_accounting(request, project_id):
    project = Project.objects.get(id=project_id)
    if request.user == project.accounting_manager and project.production_funding_request:
        tipo = request.POST.get('tipo')
        evidencia = request.POST.get('evidence') == 'true'
        project.accounting_cost_request = tipo
        project.evidence_required = evidencia
        project.save()
        # Notifica al project_manager
        Notification.objects.create(
            recipient=project.project_manager,
            sender=request.user,
            notification_type='project_update',
            project=project,
            message=f"{request.user.first_name} {request.user.last_name} assigned the type of cost request: {tipo} (Evidence required: {'Yes' if evidencia else 'No'}) for the project {project.project_name}."
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'forbidden'}, status=403)


