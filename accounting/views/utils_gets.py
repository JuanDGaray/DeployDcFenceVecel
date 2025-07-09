from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F, Q, Sum
from customer.models import Project, InvoiceProjects


@login_required
def get_accounting_manager_projects(request):
    """Get projects where user is accounting manager, grouped by status"""
    if request.method == 'POST':
        try:
            user = request.user
            
            # Get projects where user is accounting manager with all necessary fields
            projects = Project.objects.select_related(
                'customer', 'sales_advisor', 'accounting_manager', 'project_manager'
            ).filter(accounting_manager=user)
            
            # Group projects by status
            planning_projects = projects.filter(status__in=['planning_and_documentation', 'in_accounting'])
            production_projects = projects.filter(status='in_production')
            payment_projects = projects.filter(status__in=['pending_payment', 'in_production'])
            
            # Count projects in each category

            planning_awaiting_docs = planning_projects.filter(Q(document_requirements__is_completed=False) | Q(document_requirements__isnull=True))
            planning_awaiting_docs_count = planning_awaiting_docs.count()
            
            # Find all production projects that are missing required information
            # This includes projects in production status that don't have project manager, start date, or end date
            try:
                planning_blocked = production_projects.filter(
                    Q(project_manager__isnull=True) | 
                    Q(start_date__isnull=True) | 
                    Q(end_date__isnull=True)
                ).distinct()
                planning_blocked_count = planning_blocked.count()
            except Exception as e:
                planning_blocked = production_projects.none()
                planning_blocked_count = 0

            print('planning_blocked_count', planning_blocked_count)
            
            production_waiting = production_projects.filter(accounting_cost_request__isnull=True, production_funding_request__isnull=False, start_date__isnull=False, end_date__isnull=False, accounting_manager__isnull=False)
            production_waiting_count = production_waiting.count()
            print('production_waiting_count', production_waiting_count)
            
            # Count invoices for payment projects
            payment_unpaid = 0
            payment_no_invoices = 0
            project_unpaid_invoices = []
            project_no_invoices = []
            
            for project in payment_projects:
                invoices = InvoiceProjects.objects.filter(project=project)
                if invoices.exists():
                    unpaid_invoices = invoices.filter(total_paid__lt=F('total_invoice'))
                    if unpaid_invoices.exists():
                        project_unpaid_invoices.append(project)
                        payment_unpaid += 1
                else:
                    project_no_invoices.append(project)
                    payment_no_invoices += 1

            # Helper for payment section: add total_invoice and total_paid
            def queryset_to_dict_list_with_invoice_totals(queryset):
                result = []
                for project in queryset:
                    invoices = InvoiceProjects.objects.filter(project=project)
                    total_invoice = invoices.aggregate(total=Sum('total_invoice'))['total'] or 0
                    total_paid = invoices.aggregate(total=Sum('total_paid'))['total'] or 0
                    d = {
                        'id': project.id,
                        'project_name': project.project_name,
                        'status': project.status,
                        'created_at': project.created_at.isoformat() if project.created_at else None,
                        'customer': project.customer.id if project.customer else None,
                        'customer__customer_type': project.customer.customer_type if project.customer else None,
                        'customer__first_name': project.customer.first_name if project.customer else None,
                        'customer__last_name': project.customer.last_name if project.customer else None,
                        'customer__company_name': project.customer.company_name if project.customer else None,
                        'sales_advisor': project.sales_advisor.id if project.sales_advisor else None,
                        'sales_advisor__first_name': project.sales_advisor.first_name if project.sales_advisor else None,
                        'sales_advisor__last_name': project.sales_advisor.last_name if project.sales_advisor else None,
                        'accounting_manager': project.accounting_manager.id if project.accounting_manager else None,
                        'project_manager': project.project_manager.id if project.project_manager else None,
                        'estimated_cost': str(project.estimated_cost) if project.estimated_cost else None,
                        'actual_cost': str(project.actual_cost) if project.actual_cost else None,
                        'start_date': project.start_date.isoformat() if project.start_date else None,
                        'end_date': project.end_date.isoformat() if project.end_date else None,
                        'description': project.description,
                        'city': project.city,
                        'state': project.state,
                        'zip_code': project.zip_code,
                        'country': project.country,
                        'pending_amount': float(total_invoice) - float(total_paid),
                        'total_invoice': float(total_invoice),
                        'total_paid': float(total_paid),
                    }
                    result.append(d)
                return result

            # Convert querysets to list of dictionaries for JSON serialization
            def queryset_to_dict_list(queryset):
                return [
                    {
                        'id': project.id,
                        'project_name': project.project_name,
                        'status': project.status,
                        'created_at': project.created_at.isoformat() if project.created_at else None,
                        'customer': project.customer.id if project.customer else None,
                        'customer__customer_type': project.customer.customer_type if project.customer else None,
                        'customer__first_name': project.customer.first_name if project.customer else None,
                        'customer__last_name': project.customer.last_name if project.customer else None,
                        'customer__company_name': project.customer.company_name if project.customer else None,
                        'sales_advisor': project.sales_advisor.id if project.sales_advisor else None,
                        'sales_advisor__first_name': project.sales_advisor.first_name if project.sales_advisor else None,
                        'sales_advisor__last_name': project.sales_advisor.last_name if project.sales_advisor else None,
                        'accounting_manager': project.accounting_manager.id if project.accounting_manager else None,
                        'project_manager': project.project_manager.id if project.project_manager else None,
                        'estimated_cost': str(project.estimated_cost) if project.estimated_cost else None,
                        'actual_cost': str(project.actual_cost) if project.actual_cost else None,
                        'start_date': project.start_date.isoformat() if project.start_date else None,
                        'end_date': project.end_date.isoformat() if project.end_date else None,
                        'description': project.description,
                        'city': project.city,
                        'state': project.state,
                        'zip_code': project.zip_code,
                        'country': project.country,
                    }
                    for project in queryset
                ]
            
            response_data = {
                'status': 'success',
                'data': {
                    'planning': {
                        'projects_blocked': queryset_to_dict_list(planning_blocked),
                        'projects_awaiting_docs': queryset_to_dict_list(planning_awaiting_docs),
                        'awaiting_documents': planning_awaiting_docs_count,
                        'blocked_by_accounting': planning_blocked_count
                    },
                    'production': {
                        'projects_waiting': queryset_to_dict_list(production_waiting),
                        'waiting_type_request': production_waiting_count
                    },
                    'payment': {
                        'projects_unpaid': queryset_to_dict_list_with_invoice_totals(project_unpaid_invoices),
                        'projects_no_invoices': queryset_to_dict_list(project_no_invoices),
                        'unpaid_invoices': payment_unpaid,
                        'no_invoices': payment_no_invoices,
                        'projects_unpaid_invoices': queryset_to_dict_list_with_invoice_totals(project_unpaid_invoices),
                        'projects_no_invoices': queryset_to_dict_list(project_no_invoices)
                    }
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
