from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F, Q, Sum, OuterRef, Subquery, DecimalField, ExpressionWrapper, Value
from customer.models import Project, InvoiceProjects, ProposalProjects

@login_required
def get_accounting_manager_projects(request):
    """Get projects where user is accounting manager, grouped by status (optimizado)"""
    if request.method == 'POST':
        try:
            user = request.user
            projects = Project.objects.select_related(
                'customer', 'sales_advisor', 'accounting_manager', 'project_manager'
            ).filter(accounting_manager=user)

            # PLANNING
            planning_projects = projects.filter(status__in=['planning_and_documentation', 'in_accounting'])
            planning_awaiting_docs = planning_projects.filter(Q(document_requirements__is_completed=False) | Q(document_requirements__isnull=True)).distinct()
            planning_awaiting_docs_count = planning_awaiting_docs.count()
            production_projects = projects.filter(status='in_production')
            try:
                planning_blocked = production_projects.filter(
                    Q(project_manager__isnull=True) | Q(start_date__isnull=True) | Q(end_date__isnull=True)
                ).distinct()
                planning_blocked_count = planning_blocked.count()
            except Exception:
                planning_blocked = production_projects.none()
                planning_blocked_count = 0

            # PRODUCTION
            production_waiting = production_projects.filter(
                accounting_cost_request__isnull=True,
                production_funding_request__isnull=False,
                start_date__isnull=False,
                end_date__isnull=False,
                accounting_manager__isnull=False
            )
            production_waiting_count = production_waiting.count()

            # PAYMENT & BILLED PENDING (Optimizado)
            payment_projects = projects.filter(status__in=['pending_payment', 'in_production'])

            # Subqueries para facturas
            invoice_totals = InvoiceProjects.objects.filter(project=OuterRef('pk')).values('project').annotate(
                total_invoice=Sum('total_invoice'),
                total_paid=Sum('total_paid')
            )
            # Subquery para propuesta aprobada
            approved_proposal_subq = ProposalProjects.objects.filter(
                project=OuterRef('pk'),
                status=ProposalProjects.STATUS_APPROVED
            ).order_by('id')

            payment_projects_annotated = payment_projects.annotate(
                total_invoice=Subquery(invoice_totals.values('total_invoice')[:1], output_field=DecimalField()),
                total_paid=Subquery(invoice_totals.values('total_paid')[:1], output_field=DecimalField()),
                approved_proposal_id=Subquery(approved_proposal_subq.values('id')[:1]),
                approved_billed_proposal=Subquery(approved_proposal_subq.values('billed_proposal')[:1], output_field=DecimalField()),
                approved_total_proposal=Subquery(approved_proposal_subq.values('total_proposal')[:1], output_field=DecimalField()),
            )

            # PAYMENT: proyectos con facturas impagas o sin facturas
            projects_unpaid = payment_projects_annotated.filter(total_invoice__gt=0, total_paid__lt=F('total_invoice'))
            projects_no_invoices = payment_projects_annotated.filter(Q(total_invoice__isnull=True) | Q(total_invoice=0))

            # BILLED PENDING: proyectos con propuesta aprobada sin facturación o facturación incompleta
            billed_pending_projects = payment_projects_annotated.filter(
                Q(approved_proposal_id__isnull=True) |
                Q(approved_billed_proposal__lt=F('approved_total_proposal'))
            )

            # Serializadores
            def project_to_dict(project, extra_fields=None):
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
                }
                if extra_fields:
                    d.update(extra_fields)
                return d

            planning_blocked_list = [project_to_dict(p) for p in planning_blocked]
            planning_awaiting_docs_list = [project_to_dict(p) for p in planning_awaiting_docs]
            production_waiting_list = [project_to_dict(p) for p in production_waiting]

            # PAYMENT
            projects_unpaid_list = [project_to_dict(p, {
                'pending_amount': float(p.total_invoice or 0) - float(p.total_paid or 0),
                'total_invoice': float(p.total_invoice or 0),
                'total_paid': float(p.total_paid or 0),
            }) for p in projects_unpaid]
            projects_no_invoices_list = [project_to_dict(p) for p in projects_no_invoices]

            # BILLED PENDING
            billed_pending_list = []
            for p in billed_pending_projects:
                issue_type = 'No Billing' if not p.total_invoice else 'Incomplete Billing'
                if p.approved_billed_proposal == 0:
                    issue_type = 'No Billing'
                elif p.approved_billed_proposal < p.approved_total_proposal:
                    issue_type = 'Incomplete Billing'
                billed_pending_list.append(project_to_dict(p, {
                    'billed_proposal': float(p.approved_billed_proposal or 0),
                    'total_proposal': float(p.approved_total_proposal or 0),
                    'pending_billing': float(p.approved_total_proposal or 0) - float(p.approved_billed_proposal or 0),
                    'total_invoice': float(p.total_invoice or 0),
                    'total_paid': float(p.total_paid or 0),
                    'pending_amount': float(p.approved_total_proposal or 0) - float(p.total_invoice or 0),
                    'issue_type': issue_type,
                }))

            response_data = {
                'status': 'success',
                'data': {
                    'planning': {
                        'projects_blocked': planning_blocked_list,
                        'projects_awaiting_docs': planning_awaiting_docs_list,
                        'awaiting_documents': planning_awaiting_docs_count,
                        'blocked_by_accounting': planning_blocked_count
                    },
                    'production': {
                        'projects_waiting': production_waiting_list,
                        'waiting_type_request': production_waiting_count
                    },
                    'payment': {
                        'projects_unpaid': projects_unpaid_list,
                        'projects_no_invoices': projects_no_invoices_list,
                        'unpaid_invoices': projects_unpaid.count(),
                        'no_invoices': projects_no_invoices.count(),
                        'projects_unpaid_invoices': projects_unpaid_list,
                        'projects_no_invoices': projects_no_invoices_list
                    },
                    'billed_pending': {
                        'projects': billed_pending_list,
                        'count': len(billed_pending_list)
                    },
                }
            }
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
