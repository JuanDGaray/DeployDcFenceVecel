from django.contrib.auth.decorators import login_required
from customer.models import Project
from django.http import JsonResponse
from ..models import ProposalProjects, BudgetEstimate, Project, InvoiceProjects, Customer, commentsProject, ProjectHistory, Notification, ProjectDocumentRequirement
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import json
from django.shortcuts import get_object_or_404

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
    return JsonResponse(projects_by_status, safe=False)


@login_required
def get_projects(request, page=1):
        timeInitial = timezone.now()
        view = request.GET.get('view')
        allProjects = request.GET.get('all')
        sort = request.GET.get('sort')

        if (sort == '' or sort == None):
            sort = '-id'


        if view == 'view_project':
            projects = Project.objects.order_by(sort).values(
                'id', 'project_name', 'status', 
                'sales_advisor__username', 'estimated_cost', 'actual_cost', 'created_at', 'customer',
                'customer__customer_type', 'customer__first_name', 'customer__last_name', 'customer__company_name',
                'sales_advisor__first_name', 'sales_advisor__last_name',
            )
            numberProjects = 15
        else:
            projects = Project.objects.filter(sales_advisor=request.user).order_by(sort).values(
                'id', 'project_name', 'status', 
                'sales_advisor__username', 'estimated_cost', 'actual_cost', 'created_at', 'customer',
                'customer__customer_type', 'customer__first_name', 'customer__last_name', 'customer__company_name',
                'sales_advisor__first_name', 'sales_advisor__last_name', 
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
        
        # Obtener notificaciones de menciones y respuestas
        mention_notifications = []
        try:
            # Intentar obtener notificaciones de menciones (solo si el modelo existe)
            notifications = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).select_related('sender', 'project', 'comment').order_by('-date_created')[:5]
            print(notifications)
            for notification in notifications:
                mention_notifications.append({
                    'id': notification.id,
                    'title': f'{notification.get_notification_type_display()}',
                    'message': notification.message,
                    'link': f'/projects/{notification.project.id}/',
                    'type': 'primary',
                    'date': notification.date_created.strftime('%M/%d %H:%M'),
                    'sender': notification.sender.get_full_name() if notification.sender else 'System'
                })
        except Exception as e:
            # Si el modelo Notification no existe aún, continuar sin menciones
            print(f"Notification model not available: {e}")
            pass
        
        # Construcción de notificaciones
        notifications = []
        
        # Agregar notificaciones de menciones primero
        notifications.extend(mention_notifications)
        
        # Agregar notificaciones de propuestas
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

@login_required
def create_new_invoice_by_project_id(request, project_id):

        project = Project.objects.get(id=project_id)
        has_invoice = InvoiceProjects.objects.filter(project_id=project_id).exists()
        proposal = ProposalProjects.objects.filter(project_id=project_id).filter(status='approved')
        proposal_list = []
        for proposal in proposal:
            proposal_list.append({
                'id': proposal.id,
                'project_id': proposal.project.id,
                'budget_id': proposal.budget.id,
                'date': proposal.date_created,
                'project_name': proposal.project_name,
                'status': proposal.status,
                'due_date': proposal.due_date,
                'created_by': proposal.sales_advisor.get_full_name(),
                'total_proposal': proposal.total_proposal,
                'billed': proposal.billed_proposal,
            })
        if has_invoice:
            return JsonResponse({'status': 'success', 'message': 'This project already has an invoice.', 'proposal': proposal_list}, status=200)
        else:
            return JsonResponse({'status': 'success', 'message': 'Please select a proposal to create the invoice.', 'proposal': proposal_list}, status=200)

@login_required
def get_invoices(request, page=1):
        view = request.GET.get('view')
        allInvoices = request.GET.get('all')
        sort = request.GET.get('sort')

        if (sort == '' or sort == None) and not view == 'view_invoice':
            sort = '-id'
        elif view == 'view_invoice' and (sort == '' or sort == None):
            sort = 'project_name'
            
        if view == 'view_invoice':
            invoices = InvoiceProjects.objects.order_by(sort)
            numberProjects = 15
        else:
            invoices = InvoiceProjects.objects.filter(sales_advisor=request.user).order_by(sort)
            numberProjects = 10
        
        if request.GET.get('searchInputProjectId') or request.GET.get('searchInputProjectName') or request.GET.get('searchInputStatus') or request.GET.get('searchInputDueDate'):
            invoice_name = request.GET.get('searchInputInvoiceName', '')
            status = request.GET.get('searchInputStatus', '')
            due_date = request.GET.get('searchInputDueDate', '')
            invoice_id = request.GET.get('searchInputInvoiceId', '')
            filters = Q()
            if invoice_id:
                filters &= Q(id=invoice_id)
            if status:
                filters &= Q(status=status)
            if due_date:
                filters &= Q(created_at=due_date)
            # Aplica todos los filtros en una sola consulta
            invoices = invoices.filter(filters)

        # Paginación
        if allInvoices == 'true':
            numberProjects = 1000
        paginator = Paginator(invoices, numberProjects)
        page_obj = paginator.get_page(page)
        
        # Convert invoices to a list of dictionaries
        invoices_list = []
        for invoice in page_obj.object_list:
            invoice_dict = {
                'id': invoice.id,
                'project_id': invoice.project.id,
                'budget_id': invoice.budget.id,
                'project_name': invoice.project.project_name,
                'date_created': invoice.date_created.strftime('%Y-%m-%d'),
                'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else None,
                'status': invoice.status,
                'total_invoice': float(invoice.total_invoice),
                'total_paid': float(invoice.total_paid),
                'sales_advisor': invoice.sales_advisor.username if invoice.sales_advisor else None,
                'customer_type': invoice.project.customer.customer_type,
                'customer_name': invoice.project.customer.get_full_name() if invoice.project.customer.customer_type == 'individual' else invoice.project.customer.company_name,
                'percentage_paid': invoice.percentage_paid
            }
            invoices_list.append(invoice_dict)

        return JsonResponse({   
            'invoices': invoices_list,
            'has_more': page_obj.has_next(),
            'total_pages': paginator.num_pages,
            'total_invoices': paginator.count
        })

@login_required
def update_invoice_status(request, invoice_id):
    try:
        invoice = InvoiceProjects.objects.get(id=invoice_id)
        invoice.status = request.POST.get('status')
        invoice.save()
        return JsonResponse({'status': 'success', 'message': 'Status updated successfully.'})
    except InvoiceProjects.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invoice not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

import time
@login_required
def get_customers_primary_info(request):
    try:
        page = request.GET.get('page', 1)
        view = request.GET.get('view', 'view_customer')
        allCustomers = request.GET.get('all', 'false')
        sort = request.GET.get('sort', '-id')

        if sort == 'false':
            sort = '-id'

        customers = Customer.objects.only('id', 'customer_type', 'first_name', 'last_name', 'company_name', 'email', 'phone', 'status', 'sales_advisor_id',  'sales_advisor__first_name', 'sales_advisor__last_name')

        if view == 'view_customer':
            numberCustomers = 15
            customers = customers.order_by(sort)
        else:
            customers = customers.filter(sales_advisor=request.user)
            numberCustomers = 10
        
        timeInitial = time.time()
        if request.GET.get('searchInputCustomerId') or request.GET.get('searchInputCustomerName') or request.GET.get('searchInputCustomerType') or request.GET.get('searchInputCustomerEmail') or request.GET.get('searchInputSeller') or request.GET.get('searchInputCustomerCompanyOrContractor') or request.GET.get('searchInputCustomerStatus'):
            customer_name = request.GET.get('searchInputCustomerName', '')
            customer_company = request.GET.get('searchInputCustomerCompanyOrContractor', '')
            customer_type = request.GET.get('searchInputCustomerType', '')
            customer_email = request.GET.get('searchInputCustomerEmail', '')
            status = request.GET.get('searchInputStatus', '')
            seller = request.GET.get('searchInputSeller', '')
            print(seller, type(seller)) 
            filters = Q()
            if customer_name:
                filters &= Q(first_name__icontains=customer_name) | Q(last_name__icontains=customer_name) | Q(company_name__icontains=customer_name)
            if customer_type:
                filters &= Q(customer_type=customer_type)
            if customer_email:
                filters &= Q(email__icontains=customer_email)
            if status:
                filters &= Q(status=status)
            if seller:
                filters &= Q(sales_advisor_id=seller)
            if customer_company:
                filters &= Q(company_name__icontains=customer_company) | Q(first_name__icontains=customer_company) | Q(last_name__icontains=customer_company) | Q(contractor_name__icontains=customer_company)
            customers = customers.filter(filters)
        if allCustomers == 'true':
            numberCustomers = 1000

        paginator = Paginator(customers, numberCustomers)
        page_obj = paginator.get_page(page)     
        customers_list = []

        customers_list = list(page_obj.object_list.values(
            'id', 'customer_type', 'first_name', 'last_name', 'company_name', 'phone',
            'email', 'status', 'sales_advisor_id', 'sales_advisor__first_name', 'sales_advisor__last_name'
        ))
        return JsonResponse({
        'customers': customers_list,
            'has_more': page_obj.has_next(),
            'total_pages': paginator.num_pages,
            'total_customers': paginator.count
        })
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_activity_project_and_comments(request, project_id):
    try:
        # Get activities and comments (always return all data)
        activities = ProjectHistory.objects.filter(project_id=project_id).only('id', 'timestamp', 'user', 'action', 'description', 'changes', 'user__first_name', 'user__last_name', 'user__username').order_by('-timestamp')
        comments = commentsProject.objects.filter(project_id=project_id).only('id', 'comment', 'user', 'date_created', 'date_updated', 'user__first_name', 'user__last_name', 'user__username', 'parent_comment', 'mentioned_users').order_by('-date_created')
        
        # Filter activities to exclude comment activities
        activities = activities.exclude(action='COMMENT')
        
        # Combine activities and comments into a single list
        combined_items = []
        
        # Add activities
        for activity in activities:
            combined_items.append({
                'type': 'activity',
                'id': activity.id,
                'action': activity.action,
                'action_display': activity.get_action_display(),
                'description': activity.description,
                'changes': activity.changes,
                'user_name': f"{activity.user.first_name} {activity.user.last_name}".strip() if activity.user else "System",
                'user_initials': f"{activity.user.first_name[0] if activity.user and activity.user.first_name else 'S'}{activity.user.last_name[0] if activity.user and activity.user.last_name else 'Y'}".upper() if activity.user else "SY",
                'date_created': activity.timestamp.isoformat(),
            })
        
        # Add comments
        for comment in comments:
            # Get replies for this comment
            replies_data = []
            if not comment.is_reply:  # Only get replies for parent comments
                replies = comment.replies.all().order_by('date_created')
                for reply in replies:
                    replies_data.append({
                        'id': reply.id,
                        'comment': reply.comment,
                        'user_name': f"{reply.user.first_name} {reply.user.last_name}".strip() if reply.user else "Unknown",
                        'user_initials': f"{reply.user.first_name[0] if reply.user and reply.user.first_name else 'U'}{reply.user.last_name[0] if reply.user and reply.user.last_name else 'K'}".upper() if reply.user else "UK",
                        'date_created': reply.date_created.isoformat(),
                    })
            
            combined_items.append({
                'type': 'comment',
                'id': comment.id,
                'comment': comment.comment,
                'user_name': f"{comment.user.first_name} {comment.user.last_name}".strip() if comment.user else "Unknown",
                'user_initials': f"{comment.user.first_name[0] if comment.user and comment.user.first_name else 'U'}{comment.user.last_name[0] if comment.user and comment.user.last_name else 'K'}".upper() if comment.user else "UK",
                'date_created': comment.date_created.isoformat(),
                'replies': replies_data,
                'has_replies': comment.has_replies,
            })
        
        # Sort combined items by date (newest first)
        combined_items.sort(key=lambda x: x['date_created'], reverse=True)
        
        return JsonResponse({
            'status': 'success',
            'items': combined_items
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
def get_users_for_mentions(request):
    """
    Obtiene la lista de usuarios para autocompletado en menciones
    """
    try:
        search_term = request.GET.get('q', '').lower()
        
        # Obtener usuarios activos que coincidan con el término de búsqueda
        users = User.objects.filter(
            is_active=True
        ).filter(
            Q(username__icontains=search_term) |
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term)
        )[:10]  # Limitar a 10 resultados
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'initials': (user.first_name[0] if user.first_name else '') + (user.last_name[0] if user.last_name else ''),
                'email': user.email
            })
        
        return JsonResponse({
            'status': 'success',
            'users': users_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
def mark_notification_as_read(request, notification_id):
    """
    Marca una notificación como leída
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notification marked as read'
        })
        
    except Notification.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Notification not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
def mark_all_notifications_as_read(request):
    """
    Marca todas las notificaciones del usuario como leídas
    """
    try:
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        
        return JsonResponse({
            'status': 'success',
            'message': 'All notifications marked as read'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
def delete_notification(request, notification_id):
    """
    Elimina una notificación cuando el usuario la ve
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notification deleted'
        })
        
    except Notification.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Notification not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
def delete_all_notifications(request):
    """
    Elimina todas las notificaciones del usuario
    """
    try:
        Notification.objects.filter(recipient=request.user).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'All notifications deleted'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)
    

@login_required
def get_documents_checklist(request, project_id):
    try:
        documents = ProjectDocumentRequirement.objects.filter(project_id=project_id).only('id', 'type_document', 'name', 'description', 'file_url', 'is_completed', 'added_by', 'project__accounting_manager')
        request_user = request.user
        request_user_is_accounting_manager_or_admin = request_user.is_superuser or request_user.is_staff or request_user == documents.first().project.accounting_manager
        return JsonResponse({
            'documents': list(documents.values('id', 'type_document', 'name', 'description', 'file_url', 'is_completed', 'added_by__first_name', 'added_by__last_name', 'project__accounting_manager')),
            'status': 'success',
            'request_user_is_accounting_manager_or_admin': request_user_is_accounting_manager_or_admin
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

        
@login_required
def send_to_production(request):
    try:
        
        project_id = int(request.POST.get('project_id'))
        project = Project.objects.get(id=project_id)
        if request.user.is_superuser or request.user.is_staff or request.user == project.accounting_manager  or request.user == project.sales_advisor or request.user.groups.filter(name='ADMIN').exists():
            project.status = Project.STATUS_IN_PRODUCTION
            project.save()
        else:
            return JsonResponse({'status': 'error', 'message': 'You are not authorized to send this project to production'}, status=403)
        return JsonResponse({'status': 'success', 'message': 'Project sent to production'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)