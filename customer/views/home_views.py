from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render
from ..models import ProposalProjects, BudgetEstimate, Project
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def my_space(request):
    sales_advisors = User.objects.filter()
    return render(request, 'my_space.html', {'sales_advisors': sales_advisors})


@login_required
def get_proposals(request, page=1):
        
    try:
        # Obtén todas las propuestas
        proposals = ProposalProjects.objects.all().order_by('-date_created')

        # Si hay un filtro proporcionado
        if request.GET.get('projectName') or request.GET.get('status') or request.GET.get('salesAdvisor') or request.GET.get('dueDate') or request.GET.get('quoteYear') or request.GET.get('quoteMonth') or request.GET.get('quoteDay') or request.GET.get('quoteProjectId'):
            project_name = request.GET.get('projectName', '')
            status = request.GET.get('status', '')
            sales_advisor = request.GET.get('salesAdvisor', '')
            due_date = request.GET.get('dueDate', '')
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
            if sales_advisor:
                filters &= Q(sales_advisor__id=sales_advisor)
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
def get_userInfo(request, id_user):
    try:
        user = User.objects.get(id=id_user)
        userProjectsCount = Project.objects.filter(sales_advisor=user).count()
        userProposalsCount = ProposalProjects.objects.filter(sales_advisor=user, status='sent').count()
        userBudgetCount = BudgetEstimate.objects.filter(sales_advisor=user).count()
        data = {
        'user': user,
        'userProjectsCount': userProjectsCount,
        'userProposalsCount': userProposalsCount,
            'userBudgetCount': userBudgetCount
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

