from django.contrib.auth.decorators import login_required
from customer.models import Project
from django.http import JsonResponse, HttpResponse
from ..models import ProposalProjects, BudgetEstimate, Project, InvoiceProjects, Customer, commentsProject, ProjectHistory, Notification, ProjectDocumentRequirement, EmailTracking
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import json
from django.shortcuts import get_object_or_404
import os
from django.conf import settings
from django.utils.timezone import now

@login_required
def get_proposals(request, page=1):
    try:
        # Obtén todas las propuestas
        proposals = ProposalProjects.objects.all().filter(sales_advisor=request.user, status__in=['new', 'sent', 'pending', 'approved',]).order_by('-date_created')
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
            print('onlyOverdue')
            proposals = proposals.filter(due_date__lt=timezone.now().date(), status__in=['new', 'sent', 'pending'])
        elif request.GET.get('onlySoonDue') == 'true' and request.GET.get('onlyOverdue') == 'false':
            print('onlySoonDue')
            proposals = proposals.filter(due_date__lt=timezone.now().date() + timezone.timedelta(days=2), status__in=['new', 'sent', 'pending'])
        elif request.GET.get('onlyOverdue') == 'true' and request.GET.get('onlySoonDue') == 'true':
            print('both')
            proposals = proposals.filter(is_overdue=True)


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
        onlyMe = request.GET.get('only-me')
        sort = request.GET.get('sort')

        if (sort == '' or sort == None):
            sort = '-id'

        # Obtener información del usuario actual y sus permisos
        current_user = request.user
        is_admin = current_user.is_superuser or current_user.groups.filter(name='ADMIN').exists()

        # Determinar qué proyectos mostrar basado en los filtros
        if view == 'view_project':
            if onlyMe == 'true':
                # Solo proyectos del usuario actual
                projects = Project.objects.filter(sales_advisor=request.user).order_by(sort).values(
                    'id', 'project_name', 'status', 
                    'sales_advisor__username', 'estimated_cost', 'actual_cost', 'created_at', 'customer',
                    'customer__customer_type', 'customer__first_name', 'customer__last_name', 'customer__company_name',
                    'sales_advisor__first_name', 'sales_advisor__last_name', 'collaborators'
                )
            else:
                # Todos los proyectos (vista por defecto)
                projects = Project.objects.order_by(sort).values(
                    'id', 'project_name', 'status', 
                    'sales_advisor__username', 'estimated_cost', 'actual_cost', 'created_at', 'customer',
                    'customer__customer_type', 'customer__first_name', 'customer__last_name', 'customer__company_name',
                    'sales_advisor__first_name', 'sales_advisor__last_name', 'collaborators'
                )
            numberProjects = 15
        else:
            # Vista "My Projects" - siempre solo proyectos del usuario
            projects = Project.objects.filter(sales_advisor=request.user).order_by(sort).values(
                'id', 'project_name', 'status', 
                'sales_advisor__username', 'estimated_cost', 'actual_cost', 'created_at', 'customer',
                'customer__customer_type', 'customer__first_name', 'customer__last_name', 'customer__company_name',
                'sales_advisor__first_name', 'sales_advisor__last_name', 'collaborators'
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
        
        # Agregar información del usuario actual para permisos
        projects_list = list(page_obj.object_list)


        return JsonResponse({
            'projects': projects_list,
            'has_more': page_obj.has_next(),
            'total_pages': paginator.num_pages,
            'total_projects': paginator.count,
            'current_user': {
                'username': current_user.username,
                'is_admin': is_admin
            }
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
        
        proposal_counts = ProposalProjects.objects.filter(sales_advisor=request.user, status__in=['new', 'sent', 'pending']).aggregate(
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
        if not documents.exists():
            return JsonResponse({
                'status': 'success',
                'documents': [],
            }, status=200)
        request_user = request.user
        request_user_is_accounting_manager_or_admin = request_user.is_superuser or request_user.is_staff or request_user == documents.first().project.accounting_manager
        return JsonResponse({
            'documents': list(documents.values('id', 'type_document', 'name', 'description', 'file_url', 'is_completed', 'added_by__first_name', 'added_by__last_name', 'project__accounting_manager')),
            'status': 'success',
            'request_user_is_accounting_manager_or_admin': request_user_is_accounting_manager_or_admin
        })
    except Exception as e:
        print(e)
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


def generate_tracking_id():
    """
    Genera un ID único para tracking de emails
    """
    import uuid
    import hashlib
    import time
    
    # Crear un ID único basado en timestamp y UUID
    timestamp = str(int(time.time() * 1000))
    unique_id = str(uuid.uuid4())
    
    # Combinar y crear hash
    combined = f"{timestamp}_{unique_id}"
    tracking_id = hashlib.md5(combined.encode()).hexdigest()[:16]
    
    return tracking_id


def create_email_tracking(email_type, recipient_email, subject, project=None, proposal=None, invoice=None, sent_by=None, metadata=None):
    """
    Crea un registro de tracking para un email
    
    Args:
        email_type: Tipo de email ('proposal', 'invoice', 'notification', 'other')
        recipient_email: Email del destinatario
        subject: Asunto del email
        project: Proyecto relacionado (opcional)
        proposal: Propuesta relacionada (opcional)
        invoice: Factura relacionada (opcional)
        sent_by: Usuario que envió el email (opcional)
        metadata: Datos adicionales (opcional)
    
    Returns:
        EmailTracking: Instancia del registro de tracking
    """
    tracking_id = generate_tracking_id()
    
    tracking = EmailTracking.objects.create(
        tracking_id=tracking_id,
        email_type=email_type,
        recipient_email=recipient_email,
        subject=subject,
        project=project,
        proposal=proposal,
        invoice=invoice,
        sent_by=sent_by,
        metadata=metadata or {}
    )
    
    return tracking


def get_tracking_pixel_url(tracking_id):
    """
    Genera la URL del pixel de tracking
    
    Args:
        tracking_id: ID único del tracking
    
    Returns:
        str: URL completa del pixel de tracking
    """
    from django.urls import reverse
    from django.conf import settings
    
    # Construir la URL completa
    base_url = 'https://office.dcfence.org' #settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
    tracking_url = reverse('log_img_traking_email_view', kwargs={'tracking_id': tracking_id})
    
    return f"{base_url}{tracking_url}"


def add_tracking_to_email_html(html_content, tracking_id):
    """
    Agrega el pixel de tracking al HTML del email
    
    Args:
        html_content: Contenido HTML del email
        tracking_id: ID único del tracking
    
    Returns:
        str: HTML con el pixel de tracking agregado
    """
    tracking_url = get_tracking_pixel_url(tracking_id)
    
    # Crear el tag de imagen para tracking
    tracking_pixel = f'<img src="{tracking_url}" alt="" width="1" height="1" style="display:none;" />'
    
    # Agregar antes del cierre del body
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
    else:
        # Si no hay body, agregar al final
        html_content += tracking_pixel
    
    return html_content


def get_email_tracking_stats(user=None, project=None, email_type=None, days_back=30):
    """
    Obtiene estadísticas de tracking de emails
    
    Args:
        user: Usuario para filtrar (opcional)
        project: Proyecto para filtrar (opcional)
        email_type: Tipo de email para filtrar (opcional)
        days_back: Días hacia atrás para filtrar (por defecto 30)
    
    Returns:
        dict: Estadísticas de tracking
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Filtros base
    filters = {}
    if user:
        filters['sent_by'] = user
    if project:
        filters['project'] = project
    if email_type:
        filters['email_type'] = email_type
    
    # Filtro de fecha
    date_filter = timezone.now() - timedelta(days=days_back)
    filters['sent_at__gte'] = date_filter
    
    # Consultas
    total_emails = EmailTracking.objects.filter(**filters).count()
    opened_emails = EmailTracking.objects.filter(**filters, opened_count__gt=0).count()
    
    # Calcular tasa de apertura
    open_rate = (opened_emails / total_emails * 100) if total_emails > 0 else 0
    
    # Estadísticas por tipo
    stats_by_type = {}
    for email_type_choice in EmailTracking.TRACKING_TYPES:
        type_code = email_type_choice[0]
        type_filters = filters.copy()
        type_filters['email_type'] = type_code
        
        type_total = EmailTracking.objects.filter(**type_filters).count()
        type_opened = EmailTracking.objects.filter(**type_filters, opened_count__gt=0).count()
        type_rate = (type_opened / type_total * 100) if type_total > 0 else 0
        
        stats_by_type[type_code] = {
            'total': type_total,
            'opened': type_opened,
            'rate': round(type_rate, 2)
        }
    
    return {
        'total_emails': total_emails,
        'opened_emails': opened_emails,
        'open_rate': round(open_rate, 2),
        'stats_by_type': stats_by_type,
        'days_back': days_back
    }


def log_img_traking_email_view(request, tracking_id):
    """
    Vista para tracking de emails mediante pixel de imagen
    """
    try:
        # Obtener información del tracking
        from ..models import EmailTracking
        # Obtener IP y User Agent
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        # Buscar el registro de tracking
        tracking = EmailTracking.objects.filter(tracking_id=tracking_id).first()

        if tracking:
            # Verificar si el usuario está autenticado en la aplicación
            is_authenticated = request.user.is_authenticated if hasattr(request, 'user') else False
            
            # Si está autenticado, verificar si es el mismo usuario que envió el email
            if is_authenticated and tracking.sent_by and request.user == tracking.sent_by:
                # No trackear si es el mismo usuario que envió el email
                pass
            else:
                # Verificar si la IP no es del remitente
                should_track = True
                
                # Lista de IPs del servidor/desarrollo
                server_ips = ['127.0.0.1', 'localhost', '::1', '0.0.0.0']
                
                # Si la IP actual es del servidor, no trackear
                if ip_address in server_ips:
                    should_track = False
                
                # Si hay IP del remitente y coincide, no trackear
                if tracking.sender_ip and ip_address == tracking.sender_ip:
                    should_track = False
                
                # Verificar si el usuario está logueado en la aplicación
                # Si el User-Agent contiene referencias a la aplicación, no trackear
                app_indicators = [
                    'dcfence', 'office.dcfence.org', 'dcfence.vercel.app',
                    'localhost:8000', '127.0.0.1:8000'
                ]
                
                for indicator in app_indicators:
                    if indicator.lower() in user_agent.lower():
                        should_track = False
                        break
                
                # Verificar si el referer viene de la aplicación
                referer = request.META.get('HTTP_REFERER', '')
                if referer:
                    for indicator in app_indicators:
                        if indicator.lower() in referer.lower():
                            should_track = False
                            break
                
                # Solo trackear si no es del servidor, remitente o aplicación
                if should_track:
                    tracking.mark_as_opened(ip_address=ip_address, user_agent=user_agent)
        
        # Servir la imagen de tracking (1x1 pixel transparente)
        from django.http import HttpResponse
        import base64
        
        # Crear un pixel transparente de 1x1
        pixel_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')
        
        response = HttpResponse(pixel_data, content_type='image/png')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
        
    except Exception as e:
        # En caso de error, servir una imagen por defecto
        path = settings.BASE_DIR + '/customer/static/img/logoPngsm.png'
        if os.path.exists(path):
            return HttpResponse(open(path, 'rb').read(), content_type='image/png')
        else:
            # Crear un pixel transparente como fallback
            import base64
            pixel_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')
            return HttpResponse(pixel_data, content_type='image/png')


def example_send_email_with_tracking(request, proposal_id):
    """
    Ejemplo de cómo enviar un email con tracking
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        # Obtener la propuesta
        proposal = ProposalProjects.objects.get(id=proposal_id)
        
        # Crear el tracking
        tracking = create_email_tracking(
            email_type='proposal',
            recipient_email=proposal.project.customer.email,
            subject=f'Propuesta para {proposal.project_name}',
            project=proposal.project,
            proposal=proposal,
            sent_by=request.user,
            metadata={
                'proposal_amount': float(proposal.total_proposal),
                'due_date': proposal.due_date.isoformat() if proposal.due_date else None
            }
        )
        
        # Renderizar el HTML del email
        html_content = render_to_string('emails/proposal_email.html', {
            'proposal': proposal,
            'project': proposal.project,
            'customer': proposal.project.customer
        })
        
        # Agregar el pixel de tracking al HTML
        html_with_tracking = add_tracking_to_email_html(html_content, tracking.tracking_id)
        
        # Enviar el email
        send_mail(
            subject=f'Propuesta para {proposal.project_name}',
            message='',  # Mensaje de texto plano (opcional)
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[proposal.project.customer.email],
            html_message=html_with_tracking,
            fail_silently=False
        )
        
        # Actualizar el estado de la propuesta
        proposal.status = 'sent'
        proposal.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Email enviado con tracking',
            'tracking_id': tracking.tracking_id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def get_email_tracking_data(request):
    """
    Obtiene datos de tracking de emails para mostrar en dashboard
    """
    try:
        # Obtener estadísticas del usuario actual
        stats = get_email_tracking_stats(
            user=request.user,
            days_back=30
        )
        
        # Obtener emails recientes
        recent_emails = EmailTracking.objects.filter(
            sent_by=request.user
        ).order_by('-sent_at')[:10]
        
        recent_data = []
        for email in recent_emails:
            recent_data.append({
                'id': email.id,
                'tracking_id': email.tracking_id,
                'email_type': email.get_email_type_display(),
                'recipient_email': email.recipient_email,
                'subject': email.subject,
                'sent_at': email.sent_at.strftime('%Y-%m-%d %H:%M'),
                'is_opened': email.is_opened,
                'opened_count': email.opened_count,
                'opened_at': email.opened_at.strftime('%Y-%m-%d %H:%M') if email.opened_at else None,
                'project_name': email.project.project_name if email.project else None,
                'days_since_sent': email.days_since_sent
            })
        
        return JsonResponse({
            'status': 'success',
            'stats': stats,
            'recent_emails': recent_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def email_tracking_dashboard(request):
    """
    Vista para mostrar el dashboard de tracking de emails
    """
    from django.shortcuts import render
    return render(request, 'email_tracking_stats.html')
