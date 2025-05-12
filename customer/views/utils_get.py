from django.contrib.auth.decorators import login_required
from customer.models import Project
from django.http import JsonResponse
from ..models import ProposalProjects, BudgetEstimate, Project, InvoiceProjects, Customer
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import json

from django.utils.timezone import now

@login_required
def get_proposals(request, page=1):
    try:
        # Obtén todas las propuestas
        proposals = ProposalProjects.objects.all().filter(sales_advisor=request.user, status__in=['new', 'sent', 'pending', 'approved']).order_by('-date_created')
        # Si hay un filtro proporcionado
        if request.GET.get('searchInputProjectName') or request.GET.get('searchInputStatus') or request.GET.get('searchInputDueDate') or request.GET.get('quoteYear') or request.GET.get('quoteMonth') or request.GET.get('quoteDay') or request.GET.get('quoteProjectId'):
            project_name = request.GET.get('searchInputProjectName', '')
            status = request.GET.get('searchInputStatus', '')
            due_date = request.GET.get('searchInputDueDate', '')
            quote_year = request.GET.get('quoteYear', '')
            quote_month = request.GET.get('quoteMonth', '')
            quote_day = request.GET.get('quoteDay', '')
            quote_project_id = request.GET.get('quoteProjectId', '')
            filters = Q()
            if quote_year:
                filters &= Q(date_created__year='20' + quote_year)
            if quote_month:
                filters &= Q(date_created__month=quote_month)
            if quote_day:
                filters &= Q(date_created__day=quote_day)
            if quote_project_id:
                filters &= Q(project_id=quote_project_id)
            if project_name:
                filters &= Q(project_name__icontains=project_name)
            if status:
                filters &= Q(status=status)
            if due_date:
                filters &= Q(due_date=due_date)

            # Aplica todos los filtros en una sola consulta
            proposals = proposals.filter(filters)
        print(request.GET.get('onlyOverdue'))
        if request.GET.get('onlyOverdue') == 'true' and request.GET.get('onlySoonDue') == 'false':
            proposals = proposals.filter(due_date__lt=timezone.now().date())
        elif request.GET.get('onlySoonDue') == 'true' and request.GET.get('onlyOverdue') == 'false':
            proposals = proposals.filter(due_date__lt=timezone.now().date() + timezone.timedelta(days=2))
        elif request.GET.get('onlyOverdue') == 'true' and request.GET.get('onlySoonDue') == 'true':
            proposals = proposals.filter(due_date__lt=timezone.now().date() + timezone.timedelta(days=2))


        # Paginación
        paginator = Paginator(proposals, 10)  # 10 elementos por página
        page_obj = paginator.get_page(page)

        # Renderizar el HTML para la tabla
        html = render_to_string('components/info_proposal.html', {'proposals': page_obj})

        # Se devuelve la respuesta JSON con los datos
        return JsonResponse({
            'html': html,
            'has_more': page_obj.has_next(),
            'total_pages': paginator.num_pages,
            'total_proposals': paginator.count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def get_array_projects(request):
    projects = list(Project.objects.all().order_by('project_name').values())
    projects_by_status = {}
    for project in projects:
        status = project['status']
        if status not in projects_by_status:
            projects_by_status[status] = []
        projects_by_status[status].append(project)
    print(projects_by_status)
    return JsonResponse(projects_by_status, safe=False)


@login_required
def get_projects(request, page=1):
        timeInitial = timezone.now()
        view = request.GET.get('view')
        allProjects = request.GET.get('all')
        sort = request.GET.get('sort')

        if (sort == '' or sort == None) and not view == 'view_project':
            sort = '-id'
        elif view == 'view_project' and (sort == '' or sort == None):
            sort = 'project_name'
            
        print(sort)
        if view == 'view_project':
            projects = Project.objects.order_by(sort).values(
                'id', 'project_name', 'status', 
                'sales_advisor__username', 'estimated_cost', 'actual_cost', 'created_at',
                'customer__customer_type', 'customer__first_name', 'customer__last_name', 'customer__company_name'
            )
            numberProjects = 15
        else:
            projects = Project.objects.filter(sales_advisor=request.user).order_by(sort).values(
                'id', 'project_name', 'status', 
                'sales_advisor__username', 'estimated_cost', 'actual_cost', 'created_at',
                'customer__customer_type', 'customer__first_name', 'customer__last_name', 'customer__company_name'
            )
            numberProjects = 10
        
        if request.GET.get('searchInputProjectId') or request.GET.get('searchInputProjectName') or request.GET.get('searchInputStatus') or request.GET.get('searchInputDueDate'):
            project_name = request.GET.get('searchInputProjectName', '')
            status = request.GET.get('searchInputStatus', '')
            due_date = request.GET.get('searchInputDueDate', '')
            project_id = request.GET.get('searchInputProjectId', '')
            filters = Q()
            if project_id:
                filters &= Q(id=project_id)
            if status:
                filters &= Q(status=status)
            if due_date:
                filters &= Q(created_at=due_date)
            if project_name:
                filters &= Q(project_name__icontains=project_name)

            # Aplica todos los filtros en una sola consulta
            projects = projects.filter(filters)

        # Paginación
        if allProjects == 'true':
            numberProjects = 1000
        paginator = Paginator(projects, numberProjects)
        page_obj = paginator.get_page(page)
        return JsonResponse({
            'projects': list(page_obj.object_list),
            'has_more': page_obj.has_next(),
            'total_pages': paginator.num_pages,
            'total_projects': paginator.count
        })


@login_required
def get_userInfo(request):

        user = User.objects.get(id=request.user.id)
        
        project_status_choices = [
            'new', 'contacted', 'quote_sent', 'in_negotiation', 'approved', 
            'not_approved', 'in_production', 'pending_payment', 'inactive', 'cancelled'
        ]
        projects_overbudget = Project.objects.filter(
            sales_advisor=user,
            status='in_production',
            actual_cost__gt=F('estimated_cost')
        ).count()

        projects_status = {
            status.replace('_', ' ').capitalize(): Project.objects.filter(sales_advisor=user, status=status).count()
            for status in project_status_choices
        }

         # Métrica: Cantidad de propuestas por estatus
        proposals_status_choices = ['new', 'sent', 'pending', 'approved', 'rejected']
        proposals_overdue = ProposalProjects.objects.filter(sales_advisor=user, due_date__lt=timezone.now()).count()
        proposals_status = {
            status.capitalize(): ProposalProjects.objects.filter(sales_advisor=user, status=status).count()
            for status in proposals_status_choices
        }

        data = {
            'user': user,
            'countList': [
                ('Projects', Project.objects.filter(sales_advisor=user).count()),
                ('Proposals', ProposalProjects.objects.filter(sales_advisor=user).count()),
                ('Budgets', BudgetEstimate.objects.filter(sales_advisor=user).count()),
                ('Invoices', InvoiceProjects.objects.filter(sales_advisor=user).count())
            ],
            'dataChart': {
                'projects_status': projects_status,
                'proposals_status': proposals_status
            },
            'proposals_overdue': proposals_overdue,
            'projects_overbudget': projects_overbudget
        }
        html = render_to_string('components/user_metrics.html', {'dataUser': data})
        return JsonResponse({'html': html, 'dataChart': data['dataChart'], 'proposals_overdue': data['proposals_overdue'], 'projects_overbudget': data['projects_overbudget']})

@login_required
def get_proposals_quick_info(request, id_proposal):
    try:
        proposal = ProposalProjects.objects.get(id=id_proposal)
        html = render_to_string('components/proposal_quick_info.html', {'proposal': proposal})
        return JsonResponse({'html': html, 'title': proposal.project_name})
    except ProposalProjects.DoesNotExist:
        return JsonResponse({'error': 'Proposal not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def get_projects_quick_info(request, project_id):
    try:    
        project = Project.objects.get(id=project_id)
        budgets = BudgetEstimate.objects.filter(project_id=project_id, id_related_budget__isnull=True, isChangeOrder=False)
        invoices = InvoiceProjects.objects.filter(project_id=project_id)
        proposals = ProposalProjects.objects.filter(project_id=project_id)
        changes_orders = BudgetEstimate.objects.filter(project_id=project_id, isChangeOrder=True)
        budgets_with_related = BudgetEstimate.objects.filter(project_id=project_id, id_related_budget__isnull=False, isChangeOrder=False)
        budgets_dict = {}
        for budget in budgets_with_related:
            related_id = budget.id_related_budget.id  # Suponiendo que `id_related_budget` es un atributo accesible
            if related_id not in budgets_dict:
                budgets_dict[related_id] = {'budget': [budget]}
            else:
                budgets_dict[related_id]['budget'].insert(0, budget)
        html = render_to_string('components/project_quick_info.html', {'project': project,
                                                                    'is_quickInfo': True,
                                                                    'budgets': budgets,
                                                                    'budgets_dict': budgets_dict,
                                                                    'invoices': invoices,
                                                                    'proposals':proposals,
                                                                    'changes_orders': changes_orders})
        return JsonResponse({'html': html, 'title': project.project_name})
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def get_proposal_quick_info(request, proposal_id):
    try:    
        proposal = ProposalProjects.objects.get(id=proposal_id)
        html = render_to_string('components/proposal_quick_info.html', {'proposal': proposal, 'is_quickInfo': True, 'budgets': proposal.budget})
        return JsonResponse({'html': html})
    except ProposalProjects.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def update_proposal_status(request, proposal_id):
    try:
        print(request.body)
        proposal = ProposalProjects.objects.get(id=proposal_id)
        proposal.status = json.loads(request.body).get('status')
        proposal.save()
        return JsonResponse({'status': 'success', 'message': 'Status updated successfully.'})
    except ProposalProjects.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Proposal not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


from django.db.models import Count, Case, When
from django.utils.timezone import now
from datetime import timedelta
from django.http import JsonResponse

@login_required
def get_notifications(request):
    try:
        today = now().date()
        soon_due_date = today + timedelta(days=2)
        
        proposal_counts = ProposalProjects.objects.filter(sales_advisor=request.user, status__in=['new', 'sent', 'pending', 'approved']).aggregate(
            overdue=Count(Case(When(due_date__lt=today, then=1))),
            soon_due=Count(Case(When(due_date__gte=today, due_date__lt=soon_due_date, then=1)))
        )
        
        # Construcción de notificaciones
        notifications = []
        if proposal_counts['overdue'] > 0:
            notifications.append({
                'title': 'Overdue Proposals',
                'message': f'You have <strong class="text-danger fw-bold">{proposal_counts["overdue"]} overdue proposals</strong> that require your attention.',
                'link': '/home/proposals_overdue',
                'type': 'danger'
            })
        if proposal_counts['soon_due'] > 0:
            notifications.append({
                'title': 'Soon Due Proposals',
                'message': f'You have <strong class="text-warning fw-bold">{proposal_counts["soon_due"]} proposals due soon</strong> that require your attention.',
                'link': '/home/proposals_soon_due',
                'type': 'warning'
            })
        
        return JsonResponse({'notifications': notifications})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def extend_due_date(request, proposal_id):
    try:
        proposal = ProposalProjects.objects.get(id=proposal_id)
        proposal.due_date = now().date() + timedelta(days=15)  # Extend the due date by 15 days
        proposal.save()
        return JsonResponse({'status': 'success', 'message': 'Due date extended successfully.'})
    except ProposalProjects.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Proposal not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def get_customer(request):
    try:
        customers = Customer.objects.only('id', 'customer_type', 'first_name', 'last_name', 'company_name', 'email').order_by('first_name', 'company_name')
        customers_list = []
        for customer in customers:
            customers_list.append({
                'id': customer.id,
                'customer_type': customer.customer_type,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'company_name': customer.company_name,
                'email': customer.email,
                'full_name': customer.get_full_name(),
                'display_name': str(customer)  # This will use the __str__ method
            })
        return JsonResponse({'customers': customers_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
