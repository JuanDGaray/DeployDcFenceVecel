from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F, Avg
from django.utils import timezone
from datetime import timedelta
from ..models import Project, ProposalProjects, BudgetEstimate, InvoiceProjects, Customer, ProjectHistory, commentsProject, EmailTracking


def _can_view_user_profile(request, user_id):
    current_user = request.user
    if not current_user.is_authenticated:
        return False
    is_admin = current_user.is_superuser or current_user.groups.filter(name='ADMIN').exists()
    return is_admin or current_user.id == user_id


def _serialize_project_history_entry(entry):
    ts = timezone.localtime(entry.timestamp) if entry.timestamp and timezone.is_aware(entry.timestamp) else entry.timestamp
    return {
        'id': entry.id,
        'action': entry.action,
        'action_display': entry.get_action_display(),
        'timestamp': ts.strftime('%Y-%m-%d %H:%M') if ts else '',
        'timestamp_display': ts.strftime('%b %d, %Y %H:%M') if ts else '',
        'description': entry.description or '',
        'project_id': entry.project_id,
        'project_name': entry.project.project_name if entry.project else '',
        'changes': entry.changes or {},
        'has_changes': bool(entry.changes),
    }

def get_active_users():
    User = get_user_model()
    sessions = Session.objects.filter(expire_date__gte=now())  # Sesiones no expiradas
    user_ids = []  # IDs de usuarios con sesiones activas

    for session in sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')  # Extrae el ID del usuario
        if user_id:
            user_ids.append(user_id)

    return User.objects.filter(id__in=user_ids)

@login_required
def active_users_view(request):
    users = get_active_users()
    user_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
    return JsonResponse({'active_users': user_data})

@login_required
def user_detail_view(request, user_id):
    """
    Vista optimizada para mostrar detalles de un usuario con métricas importantes
    """
    # Obtener el usuario con sus grupos
    user = get_object_or_404(User.objects.prefetch_related('groups'), id=user_id)
    
    current_user = request.user
    is_admin = current_user.is_superuser or current_user.groups.filter(name='ADMIN').exists()
    is_viewing_own_profile = current_user.id == user_id

    if not _can_view_user_profile(request, user_id):
        return render(request, 'project_access_restricted.html', {
            'message': 'Solo los administradores pueden ver los detalles de otros usuarios.',
            'title': 'Acceso Restringido'
        })
    
    # Obtener grupos del usuario
    user_groups = user.groups.all()
    is_sales = user_groups.filter(name='SALES').exists()
    is_production = user_groups.filter(name='PRODUCTION').exists()
    is_admin_user = user_groups.filter(name='ADMIN').exists() or user.is_superuser
    
    # Consulta base optimizada para proyectos
    projects_base = Project.objects.select_related('customer').filter(sales_advisor=user)
    
    # Obtener todas las métricas de proyectos en una sola consulta agregada
    projects_stats = projects_base.aggregate(
        total_projects=Count('id'),
        total_estimated_cost=Sum('estimated_cost'),
        total_actual_cost=Sum('actual_cost'),
        overbudget_count=Count('id', filter=Q(actual_cost__gt=F('estimated_cost'), estimated_cost__gt=0)),
        completed_count=Count('id', filter=Q(status__in=['completed', 'closed'])),
        in_production_count=Count('id', filter=Q(status='in_production')),
        pending_payment_count=Count('id', filter=Q(status='pending_payment')),
        recent_projects_count=Count('id', filter=Q(created_at__gte=timezone.now() - timedelta(days=30)))
    )
    
    # Obtener estadísticas de proyectos por estado en una sola consulta
    project_status_counts = projects_base.values('status').annotate(
        count=Count('id')
    ).filter(count__gt=0)
    
    # Convertir a diccionario para el template
    project_status_stats = {}
    for item in project_status_counts:
        status = item['status']
        for status_choice, label in Project.STATUS_CHOICES:
            if status_choice == status:
                project_status_stats[status] = {
                    'count': item['count'],
                    'label': label
                }
                break
    
    # Obtener proyectos por rol en consultas separadas optimizadas
    projects_by_role = {
        'sales_advisor': projects_stats['total_projects'],
        'project_manager': Project.objects.filter(project_manager=user).count(),
        'accounting_manager': Project.objects.filter(accounting_manager=user).count(),
        'collaborator': Project.objects.filter(collaborators=user).count()
    }
    
    # Obtener métricas de propuestas en una sola consulta
    proposals_base = ProposalProjects.objects.filter(sales_advisor=user)
    proposals_stats = proposals_base.aggregate(
        total_proposals=Count('id'),
        overdue_count=Count('id', filter=Q(
            due_date__lt=timezone.now().date(),
            status__in=['new', 'sent', 'pending']
        )),
        soon_due_count=Count('id', filter=Q(
            due_date__lt=timezone.now().date() + timedelta(days=2),
            due_date__gte=timezone.now().date(),
            status__in=['new', 'sent', 'pending']
        )),
        recent_proposals_count=Count('id', filter=Q(
            date_created__gte=timezone.now() - timedelta(days=30)
        ))
    )
    
    # Obtener estadísticas de propuestas por estado
    proposal_status_counts = proposals_base.values('status').annotate(
        count=Count('id')
    ).filter(count__gt=0)
    
    proposals_by_status = {}
    for item in proposal_status_counts:
        status = item['status']
        for status_choice, label in ProposalProjects.STATUS_CHOICES:
            if status_choice == status:
                proposals_by_status[status] = {
                    'count': item['count'],
                    'label': label
                }
                break
    
    # Obtener métricas de presupuestos y facturas en consultas optimizadas
    budgets_stats = BudgetEstimate.objects.filter(sales_advisor=user).aggregate(
        total_budgets=Count('id'),
        change_orders_count=Count('id', filter=Q(isChangeOrder=True))
    )
    
    invoices_stats = InvoiceProjects.objects.filter(sales_advisor=user).aggregate(
        total_invoices=Count('id'),
        total_invoiced=Sum('total_invoice'),
        total_paid=Sum('total_paid')
    )
    
    # Obtener métricas de clientes
    customers_count = Customer.objects.filter(sales_advisor=user).count()
    
    # Obtener comentarios recientes
    recent_comments = commentsProject.objects.filter(
        user=user,
        date_created__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    project_activities_qs = ProjectHistory.objects.select_related('project').filter(user=user)
    total_activity_count = project_activities_qs.count()
    project_activities = project_activities_qs.order_by('-timestamp')[:10]
    
    # Obtener emails enviados (si existe el modelo EmailTracking)
    email_stats = {}
    try:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        email_stats = EmailTracking.objects.filter(sent_by=user).aggregate(
            recent_emails=Count('id', filter=Q(sent_at__gte=thirty_days_ago)),
            total_emails=Count('id'),
            opened_emails=Count('id', filter=Q(opened_count__gt=0))
        )
        
        total_emails = email_stats['total_emails'] or 0
        opened_emails = email_stats['opened_emails'] or 0
        
        email_stats.update({
            'open_rate': (opened_emails / total_emails * 100) if total_emails > 0 else 0
        })
    except:
        email_stats = {
            'recent_emails': 0,
            'total_emails': 0,
            'opened_emails': 0,
            'open_rate': 0
        }
    
    # Obtener proyectos más importantes (por costo estimado) - limitado a 5
    top_projects = projects_base.filter(
        estimated_cost__gt=0
    ).select_related('customer').order_by('-estimated_cost')[:5]
    
    # Obtener proyectos recientes - limitado a 5
    recent_projects_list = projects_base.select_related('customer').order_by('-created_at')[:5]
    
    # Obtener proyectos activos - limitado a 5
    active_projects = projects_base.filter(
        status='in_production'
    ).select_related('customer')[:5]
    
    # Obtener proyectos pendientes de pago - limitado a 5
    pending_payment_projects = projects_base.filter(
        status='pending_payment'
    ).select_related('customer')[:5]
    
    # Calcular eficiencia y rentabilidad
    total_projects = projects_stats['total_projects'] or 0
    completed_projects = projects_stats['completed_count'] or 0
    completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
    
    # Calcular rentabilidad promedio
    profitable_projects_stats = projects_base.filter(
        actual_cost__gt=0,
        estimated_cost__gt=0
    ).aggregate(
        avg_profit_margin=Avg(F('estimated_cost') - F('actual_cost'))
    )
    
    avg_profit_margin = profitable_projects_stats['avg_profit_margin'] or 0
    
    # Preparar contexto optimizado
    context = {
        'user': user,
        'user_groups': user_groups,
        'is_sales': is_sales,
        'is_production': is_production,
        'is_admin_user': is_admin_user,
        'is_admin': is_admin,
        'is_viewing_own_profile': is_viewing_own_profile,
        'current_user': current_user,
        
        # Métricas principales
        'project_status_stats': project_status_stats,
        'projects_by_role': projects_by_role,
        'proposals_by_status': proposals_by_status,
        
        # Métricas financieras
        'total_estimated_cost': projects_stats['total_estimated_cost'] or 0,
        'total_actual_cost': projects_stats['total_actual_cost'] or 0,
        'overbudget_projects': projects_stats['overbudget_count'] or 0,
        'avg_profit_margin': avg_profit_margin,
        
        # Contadores
        'projects_count': total_projects,
        'proposals_count': proposals_stats['total_proposals'] or 0,
        'budgets_count': budgets_stats['total_budgets'] or 0,
        'change_orders_count': budgets_stats['change_orders_count'] or 0,
        'invoices_count': invoices_stats['total_invoices'] or 0,
        'customers_count': customers_count,
        'completed_projects': completed_projects,
        'completion_rate': completion_rate,
        
        # Métricas de tiempo
        'overdue_proposals': proposals_stats['overdue_count'] or 0,
        'soon_due_proposals': proposals_stats['soon_due_count'] or 0,
        'recent_projects': projects_stats['recent_projects_count'] or 0,
        'recent_proposals': proposals_stats['recent_proposals_count'] or 0,
        'recent_comments': recent_comments,
        
        # Métricas financieras detalladas
        'total_invoiced': invoices_stats['total_invoiced'] or 0,
        'total_paid': invoices_stats['total_paid'] or 0,
        'outstanding_amount': (invoices_stats['total_invoiced'] or 0) - (invoices_stats['total_paid'] or 0),
        
        # Actividad
        'project_activities': project_activities,
        'total_activity_count': total_activity_count,
        'activity_action_choices': ProjectHistory.ACTION_TYPES,
        'email_stats': email_stats,
        
        # Listas de proyectos
        'top_projects': top_projects,
        'recent_projects_list': recent_projects_list,
        'active_projects': active_projects,
        'pending_payment_projects': pending_payment_projects,
    }
    
    return render(request, 'user_detail.html', context)


@login_required
def user_activity_history_api(request, user_id):
    if not _can_view_user_profile(request, user_id):
        return JsonResponse({'error': 'Access denied'}, status=403)

    user = get_object_or_404(User, id=user_id)
    page = request.GET.get('page', 1)
    action_filter = request.GET.get('action', '').strip()
    search_query = request.GET.get('q', '').strip()

    try:
        per_page = min(max(int(request.GET.get('per_page', 20)), 5), 50)
    except (TypeError, ValueError):
        per_page = 20

    queryset = ProjectHistory.objects.select_related('project').filter(user=user)

    if action_filter:
        queryset = queryset.filter(action=action_filter)

    if search_query:
        queryset = queryset.filter(
            Q(description__icontains=search_query)
            | Q(project__project_name__icontains=search_query)
        )

    queryset = queryset.order_by('-timestamp')
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    return JsonResponse({
        'activities': [_serialize_project_history_entry(entry) for entry in page_obj.object_list],
        'pagination': {
            'page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'per_page': per_page,
        },
        'user': {
            'id': user.id,
            'full_name': user.get_full_name() or user.username,
        },
    })
