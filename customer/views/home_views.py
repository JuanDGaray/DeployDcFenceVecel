from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.utils import timezone
from django.shortcuts import render
from ..models import ProposalProjects, BudgetEstimate, Project, InvoiceProjects
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def my_space(request):
    sales_advisors = User.objects.filter()
    user_id = request.user.id
    return render(request, 'my_space.html', {'sales_advisors': sales_advisors, 'user_id': user_id})


@login_required
def get_proposals(request, page=1):
    try:
        # Obtén todas las propuestas
        proposals = ProposalProjects.objects.all().filter(sales_advisor=request.user).order_by('-date_created')
        print(request.GET)
        # Si hay un filtro proporcionado
        if request.GET.get('searchInputProjectName') or request.GET.get('searchInputStatus') or request.GET.get('searchInputDueDate') or request.GET.get('quoteYear') or request.GET.get('quoteMonth') or request.GET.get('quoteDay') or request.GET.get('quoteProjectId'):
            project_name = request.GET.get('searchInputProjectName', '')
            status = request.GET.get('searchInputStatus', '')
            due_date = request.GET.get('searchInputDueDate', '')
            quote_year = request.GET.get('quoteYear', '')
            quote_month = request.GET.get('quoteMonth', '')
            quote_day = request.GET.get('quoteDay', '')
            quote_project_id = request.GET.get('quoteProjectId', '')
            print(quote_year, quote_month, quote_day, quote_project_id, status, due_date, project_name)
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
def get_projects(request, page=1):

        # Obtén todas las propuestas
        projects = Project.objects.all().filter(sales_advisor=request.user).order_by('-created_at')
        # Si hay un filtro proporcionado
        if request.GET.get('searchInputProjectName') or request.GET.get('searchInputStatus') or request.GET.get('searchInputDueDate') or request.GET.get('ProjectId'):
            project_name = request.GET.get('searchInputProjectName', '')
            status = request.GET.get('searchInputStatus', '')
            due_date = request.GET.get('searchInputDueDate', '')
            project_id = request.GET.get('ProjectId', '')
            print(project_id, status, due_date, project_name)
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
        paginator = Paginator(projects, 10)  # 10 elementos por página
        page_obj = paginator.get_page(page)

        # Renderizar el HTML para la tabla
        html = render_to_string('components/info_project.html', {'projects': page_obj})

        # Se devuelve la respuesta JSON con los datos
        return JsonResponse({
            'html': html,
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


