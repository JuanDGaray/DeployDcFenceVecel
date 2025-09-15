from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from ..models import Project, BudgetEstimate, RealCostProject, ProposalProjects, InvoiceProjects
from django.contrib.auth.models import User
import json

def is_admin(user):
    """Verifica si el usuario es administrador"""
    user.groups.filter(name='ADMIN').exists()
    return user.is_superuser or user.is_staff or user.groups.filter(name='ADMIN').exists()

@login_required
@user_passes_test(is_admin)
def completed_projects_dashboard(request):
    """
    Vista principal del dashboard de proyectos terminados para administradores.
    Muestra proyectos organizados por año y mes.
    """
    # Obtener todos los proyectos con estado 'completed'
    completed_projects = Project.objects.filter(status='completed').order_by('-end_date')
    
    # Organizar proyectos por año y mes
    projects_by_period = {}
    
    for project in completed_projects:
        if project.end_date:
            year = project.end_date.year
            month = project.end_date.month
            
            if year not in projects_by_period:
                projects_by_period[year] = {}
            
            if month not in projects_by_period[year]:
                projects_by_period[year][month] = []
            
            # Calcular totales del proyecto
            project_totals = calculate_project_totals(project)
            
            projects_by_period[year][month].append({
                'project': project,
                'totals': project_totals
            })
    
    # Calcular totales por período
    period_totals = {}
    for year in projects_by_period:
        period_totals[year] = {}
        for month in projects_by_period[year]:
            projects = projects_by_period[year][month]
            period_totals[year][month] = {
                'total_budgeted': sum(p['totals']['budgeted_cost'] for p in projects),
                'total_actual': sum(p['totals']['actual_cost'] for p in projects),
                'total_profit': sum(p['totals']['profit'] for p in projects),
                'project_count': len(projects)
            }
    
    # Calcular profit total
    total_profit = 0
    for project in completed_projects:
        project_totals = calculate_project_totals(project)
        total_profit += project_totals['profit']
    
    context = {
        'projects_by_period': projects_by_period,
        'period_totals': period_totals,
        'total_completed_projects': completed_projects.count(),
        'total_budgeted_cost': sum(p.estimated_cost or 0 for p in completed_projects),
        'total_actual_cost': sum(p.actual_cost or 0 for p in completed_projects),
        'total_profit': total_profit,
    }
    
    return render(request, 'admin/completed_projects_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def get_project_details_ajax(request, project_id):
    """
    Vista AJAX para obtener detalles completos de un proyecto específico.
    Incluye costo presupuestado, costo real y utilidad.
    """
    try:
        project = Project.objects.get(id=project_id, status='completed')
        
        # Obtener información detallada del proyecto
        project_details = get_detailed_project_info(project)
        
        return JsonResponse({
            'success': True,
            'project': project_details
        })
        
    except Project.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Proyecto no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def calculate_project_totals(project):
    """
    Calcula los totales de un proyecto completado.
    Retorna un diccionario con costo presupuestado, costo real y utilidad.
    """
    # Obtener el presupuesto aprobado (última versión)
    approved_proposal = project.get_approved_proposal()
    change_orders = project.budget_categories.filter(isChangeOrder=True, status='approved')

    invoices = project.invoices.all()
    total_invoiced = sum((invoice.total_invoice or Decimal('0')) for invoice in invoices)

    approved_total_value = (approved_proposal.total_proposal if approved_proposal and approved_proposal.total_proposal else Decimal('0'))
    approved_cost_budget = (approved_proposal.budget.projected_cost if approved_proposal and approved_proposal.budget and approved_proposal.budget.projected_cost else Decimal('0'))

    if change_orders.count() > 0:
        change_budget = sum((co.budget.total_change_order or Decimal('0')) for co in change_orders)
        budgeted_cost = approved_total_value + change_budget
        cost_budget = approved_cost_budget + change_budget
    else:
        budgeted_cost = approved_total_value
        cost_budget = approved_cost_budget

    

    actual_cost = project.actual_cost or Decimal('0')
    profit = budgeted_cost - actual_cost

    percentage_profit = float((profit / budgeted_cost * Decimal('100')) if budgeted_cost > 0 else Decimal('0'))
    
    return {
        'budgeted_cost': float(budgeted_cost),
        'actual_cost': float(actual_cost),
        'total_cost_budget': float(cost_budget),
        'total_invoiced': float(total_invoiced),
        'total_proposals': float(approved_total_value),
        'profit': float(profit),
        'profit_margin': float((profit / budgeted_cost * Decimal('100')) if budgeted_cost > 0 else Decimal('0')),
        'cost_difference': float(cost_budget - actual_cost),
        'percentage_profit': float(percentage_profit)
    }

def get_detailed_project_info(project):
    """
    Obtiene información detallada de un proyecto para mostrar en el modal.
    """
    # Información básica del proyecto
    project_info = {
        'id': project.id,
        'name': project.project_name,
        'customer': project.customer.get_full_name(),
        'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else None,
        'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
        'sales_advisor': project.sales_advisor.get_full_name() if project.sales_advisor else 'No asignado',
        'project_manager': project.project_manager.get_full_name() if project.project_manager else 'No asignado',
        'city': project.city,
        'state': project.state,
        'description': project.description or 'Sin descripción'
    }
    
    # Información de presupuestos
    budgets = project.budget_categories.filter(
        status__in=['completed', 'billed']
    ).order_by('-version_budget')
    
    budget_info = []
    for budget in budgets:
        budget_info.append({
            'version': budget.version_budget,
            'projected_cost': float(budget.projected_cost or 0),
            'profit_value': float(budget.profit_value or 0),
            'total_value': float(budget.total_value or 0),
            'status': budget.get_status_display(),
            'date_created': budget.date_created.strftime('%Y-%m-%d %H:%M')
        })
    
    # Información de propuestas
    proposals = project.proposals.filter(status='approved').order_by('-date_created')
    proposal_info = []
    for proposal in proposals:
        proposal_info.append({
            'tracking_id': proposal.tracking_id,
            'total_proposal': float(proposal.total_proposal),
            'billed_amount': float(proposal.billed_proposal),
            'remaining_amount': float(proposal.remaining_amount),
            'date_created': proposal.date_created.strftime('%Y-%m-%d'),
            'due_date': proposal.due_date.strftime('%Y-%m-%d') if proposal.due_date else None
        })
    
    # Información de facturas
    invoices = project.invoices.all().order_by('-date_created')
    invoice_info = []
    for invoice in invoices:
        invoice_info.append({
            'id': invoice.id,
            'subtotal': float(invoice.subtotal),
            'tax': float(invoice.tax),
            'retention': float(invoice.retention),
            'total_invoice': float(invoice.total_invoice),
            'total_paid': float(invoice.total_paid),
            'status': invoice.get_status_display(),
            'date_created': invoice.date_created.strftime('%Y-%m-%d'),
            'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else None
        })
    
    # Información de costos reales
    real_costs = project.cost_items.all()
    real_cost_info = []
    for cost in real_costs:
        real_cost_info.append({
            'total': cost.total,
            'evidence_url': cost.evidence_url,
            'items_count': len(cost.items) if cost.items else 0
        })
    
    # Totales generales
    totals = calculate_project_totals(project)
    
    return {
        'project': project_info,
        'budgets': budget_info,
        'proposals': proposal_info,
        'invoices': invoice_info,
        'real_costs': real_cost_info,
        'totals': totals
    }

@login_required
@user_passes_test(is_admin)
def export_completed_projects_data(request):
    """
    Vista para exportar datos de proyectos completados en formato JSON o CSV.
    """
    # Obtener todos los proyectos completados
    completed_projects = Project.objects.filter(status='completed').order_by('-end_date')
    
    export_data = []
    
    for project in completed_projects:
        totals = calculate_project_totals(project)
        
        export_data.append({
            'project_id': project.id,
            'project_name': project.project_name,
            'customer': project.customer.get_full_name(),
            'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else None,
            'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
            'sales_advisor': project.sales_advisor.get_full_name() if project.sales_advisor else 'No asignado',
            'project_manager': project.project_manager.get_full_name() if project.project_manager else 'No asignado',
            'city': project.city,
            'state': project.state,
            'budgeted_cost': totals['budgeted_cost'],
            'actual_cost': totals['actual_cost'],
            'total_proposals': totals['total_proposals'],
            'total_invoiced': totals['total_invoiced'],
            'profit': totals['profit'],
            'profit_margin': totals['profit_margin']
        })
    
    return JsonResponse({
        'success': True,
        'data': export_data,
        'total_projects': len(export_data)
    })
