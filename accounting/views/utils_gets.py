from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F, Q, Sum, OuterRef, Subquery, DecimalField, Value
from django.db.models.functions import Coalesce
from customer.models import Project, InvoiceProjects, ProposalProjects


def _user_is_admin(user):
    return bool(
        user
        and (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name='ADMIN').exists()
        )
    )


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@login_required
def get_accounting_manager_projects(request):
    """Get accounting-alert projects. Accounting managers see their projects; admins see all."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        user = request.user
        projects = Project.objects.select_related(
            'customer', 'sales_advisor', 'accounting_manager', 'project_manager'
        )
        if not _user_is_admin(user):
            projects = projects.filter(accounting_manager=user)

        # PLANNING
        planning_projects = projects.filter(status__in=['planning_and_documentation', 'in_accounting'])
        planning_awaiting_docs = planning_projects.filter(
            Q(document_requirements__is_completed=False) | Q(document_requirements__isnull=True)
        ).distinct()
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
            accounting_manager__isnull=False,
        )
        production_waiting_count = production_waiting.count()

        # After production closes, projects go to pending_payment for accounting to finish.
        payment_projects = projects.filter(
            Q(status='pending_payment') | Q(production_closed=True, status='in_production')
        )

        invoice_totals = InvoiceProjects.objects.filter(project=OuterRef('pk')).values('project').annotate(
            total_invoice=Sum('total_invoice'),
            total_paid=Sum('total_paid'),
        )
        approved_proposal_subq = ProposalProjects.objects.filter(
            project=OuterRef('pk'),
            status=ProposalProjects.STATUS_APPROVED,
        ).order_by('id')

        payment_projects_annotated = payment_projects.annotate(
            total_invoice=Coalesce(
                Subquery(invoice_totals.values('total_invoice')[:1], output_field=DecimalField()),
                Value(0),
                output_field=DecimalField(),
            ),
            total_paid=Coalesce(
                Subquery(invoice_totals.values('total_paid')[:1], output_field=DecimalField()),
                Value(0),
                output_field=DecimalField(),
            ),
            approved_proposal_id=Subquery(approved_proposal_subq.values('id')[:1]),
            approved_billed_proposal=Coalesce(
                Subquery(
                    approved_proposal_subq.values('billed_proposal')[:1],
                    output_field=DecimalField(),
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            approved_total_proposal=Coalesce(
                Subquery(
                    approved_proposal_subq.values('total_proposal')[:1],
                    output_field=DecimalField(),
                ),
                Value(0),
                output_field=DecimalField(),
            ),
        )

        projects_unpaid = payment_projects_annotated.filter(
            total_invoice__gt=0,
            total_paid__lt=F('total_invoice'),
        )
        projects_no_invoices = payment_projects_annotated.filter(total_invoice=0)

        billed_pending_projects = payment_projects_annotated.filter(
            Q(approved_proposal_id__isnull=True)
            | Q(approved_billed_proposal__lt=F('approved_total_proposal'))
        )

        def project_to_dict(project, extra_fields=None):
            created = getattr(project, 'created_at', None) or getattr(project, 'date_created', None)
            d = {
                'id': project.id,
                'project_name': project.project_name,
                'status': project.status,
                'created_at': created.isoformat() if created else None,
                'production_closed': bool(project.production_closed),
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
                'estimated_cost': str(project.estimated_cost) if project.estimated_cost is not None else None,
                'actual_cost': str(project.actual_cost) if project.actual_cost is not None else None,
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

        projects_unpaid_list = [
            project_to_dict(p, {
                'pending_amount': _safe_float(p.total_invoice) - _safe_float(p.total_paid),
                'total_invoice': _safe_float(p.total_invoice),
                'total_paid': _safe_float(p.total_paid),
                'payment_issue': 'unpaid_invoices',
            })
            for p in projects_unpaid
        ]
        projects_no_invoices_list = [
            project_to_dict(p, {
                'pending_amount': _safe_float(getattr(p, 'approved_total_proposal', 0)),
                'total_invoice': 0,
                'total_paid': 0,
                'payment_issue': 'no_invoices',
            })
            for p in projects_no_invoices
        ]

        billed_pending_list = []
        for p in billed_pending_projects:
            billed = _safe_float(p.approved_billed_proposal)
            total_proposal = _safe_float(p.approved_total_proposal)
            total_invoice = _safe_float(p.total_invoice)
            total_paid = _safe_float(p.total_paid)

            if not p.approved_proposal_id or billed <= 0:
                issue_type = 'No Billing'
            elif billed < total_proposal:
                issue_type = 'Incomplete Billing'
            else:
                issue_type = 'Incomplete Billing'

            billed_pending_list.append(project_to_dict(p, {
                'billed_proposal': billed,
                'total_proposal': total_proposal,
                'pending_billing': max(total_proposal - billed, 0),
                'total_invoice': total_invoice,
                'total_paid': total_paid,
                'pending_amount': max(total_proposal - total_invoice, 0),
                'issue_type': issue_type,
            }))

        response_data = {
            'status': 'success',
            'data': {
                'planning': {
                    'projects_blocked': planning_blocked_list,
                    'projects_awaiting_docs': planning_awaiting_docs_list,
                    'awaiting_documents': planning_awaiting_docs_count,
                    'blocked_by_accounting': planning_blocked_count,
                },
                'production': {
                    'projects_waiting': production_waiting_list,
                    'waiting_type_request': production_waiting_count,
                },
                'payment': {
                    'projects_unpaid': projects_unpaid_list,
                    'projects_no_invoices': projects_no_invoices_list,
                    'unpaid_invoices': len(projects_unpaid_list),
                    'no_invoices': len(projects_no_invoices_list),
                    'projects_unpaid_invoices': projects_unpaid_list,
                },
                'billed_pending': {
                    'projects': billed_pending_list,
                    'count': len(billed_pending_list),
                },
            },
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=500)
