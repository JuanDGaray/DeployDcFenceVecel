from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.core.serializers import serialize
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from ..models import (Customer, Project, 
                      BudgetEstimate, BudgetEstimateMaterialData, BudgetEstimateDeductsData,
                      BudgetEstimateLaborData, BudgetEstimateContractorData,
                      BudgetEstimateMiscData, BudgetEstimateProfitData, BudgetEstimateUtil, InvoiceProjects, ProposalProjects, ProjectBudgetXLSX)
from django.db.models import Max
from ..form import CustomerForm, ProjectsForm 
from django.core.paginator import Paginator
from django.utils.text import capfirst
from decimal import Decimal
from django.db.models import Sum, F
from django.http import HttpResponse, JsonResponse, request
from datetime import date, timedelta
from django.utils import timezone
import json
import math
from django.db import transaction
from django.conf import settings
import os
from ..utils import create_folders_by_projects, delete_folders_by_projects, new_aia5_xlxs_template
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import datetime


from groq import Groq
from ..promts import basePromt, AsisPromt,  QueryReviewPrompt, ModelReviewPrompt, AnalysiData, SystemPromtReviewData
import re, traceback
from typing import Optional, List
from pydantic import BaseModel
from customer.models import ProjectHistory

client = Groq(
    api_key="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",
)


def aiaInvoice10(request,project_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    proposal = get_object_or_404(ProposalProjects, id=invoice_id)

    if request.method == 'GET':
        return render(request, 'AIA10.html', {
            'project': project,
            'proposal':proposal,
            'today': timezone.now().date(),},)
    elif request.method == 'POST':
        data = json.loads(request.body)
        saleAdvisor = request.user
        save_invoice(data, project, proposal.budget , proposal, saleAdvisor)
        print(data)
        return HttpResponse(status=200)
    
    
def aiaInvoice5(request,project_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    proposal = get_object_or_404(ProposalProjects, id=invoice_id)

    if request.method == 'GET':
        return render(request, 'AIA5.html', {
            'project': project,
            'proposal':proposal,
            'today': timezone.now().date(),},)
    elif request.method == 'POST':
        data = json.loads(request.body)
        saleAdvisor = request.user
        save_invoice(data, project, proposal.budget , proposal, saleAdvisor)
        print(data)
        return HttpResponse(status=200)
    
    
def MdcpInvoice(request,project_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    proposal = get_object_or_404(ProposalProjects, id=invoice_id)
    next_invoice_id = (InvoiceProjects.objects.aggregate(Max('id'))['id__max'] or 0) + 1

    if request.method == 'GET':
        return render(request, 'MDCPInvoice.html', {
            'project': project,
            'proposal':proposal,
            'today': timezone.now().date(),
            'next_invoice_id': next_invoice_id,})
        
    elif request.method == 'POST':
        data = json.loads(request.body)
        saleAdvisor = request.user
        save_invoice(data, project, proposal.budget , proposal, saleAdvisor)
        return HttpResponse(status=200)
    
def BroadInvoice10(request,project_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    proposal = get_object_or_404(ProposalProjects, id=invoice_id)
    next_invoice_id = (InvoiceProjects.objects.aggregate(Max('id'))['id__max'] or 0) + 1


    if request.method == 'GET':
        return render(request, 'BrodInvoice.html', {
            'project': project,
            'proposal':proposal,
            'today': timezone.now().date(),
            'next_invoice_id': next_invoice_id,})
    elif request.method == 'POST':
        return HttpResponse(status=200)

def changePaidInvoice(request,project_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    invoice = get_object_or_404(InvoiceProjects, id=invoice_id)
    if request.method == 'POST':
        print(request.body)
        data = json.loads(request.body)
        invoice.total_paid = data['amount']
        invoice.save()
        return HttpResponse(status=200)

def get_timeline_steps(project):
    status_choices = Project.STATUS_CHOICES
    current_status_index = next(index for index, (status, _) in enumerate(status_choices) if status.lower() == project.status)
    print(project.status)
    steps = []
    for index, (status, label) in enumerate(status_choices):
        if status not in ["not_approved", "inactive", "cancelled"] :
            step = {
                'status': status,
                'title': capfirst(label),
                'is_active': index <= current_status_index,
                'is_current': index == current_status_index
            }
            steps.append(step)
        elif current_status_index == index:
            if steps:
                steps[-1]['title'] = capfirst(label)
                steps[-1]['is_current'] = "danger"

    return steps

@login_required
def projects(request):
    # Asegúrate de que la consulta esté ordenada para evitar el UnorderedObjectListWarning
    Project_list = Project.objects.all().order_by('project_name')  # Puedes cambiar por el campo que desees
    paginator = Paginator(Project_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    sellers = User.objects.all()
    customers = Customer.objects.all()
    current_user = request.user

    if request.method == 'GET':
        # Renders the customer list view with pagination
        return render(request, 'projects.html', {
            'form': ProjectsForm(),
            'projects': page_obj,
            'total_projects': Project_list.count(),
            'view': 'projects',
            'current_user': current_user,
            'customers': customers,
            'sellers': sellers
        })
    else:  # If the request method is POST
        try:
            form = ProjectsForm(request.POST)
            if form.is_valid():
                new_project = form.save(commit=False)
                new_project.sales_advisor = request.user
                new_project.status = "new"
                folder_name = new_project.project_name
                create_folder_response = create_folders_by_projects(folder_name)
                if create_folder_response['status'] == 'success':
                    new_project.folder_id = create_folder_response['folder_id']
                    new_project.save()

                return redirect('projects')
                
            else:
                return render(request, 'projects.html', {
                    'form': form,
                    'projects': page_obj,
                    'total_projects': Project_list.count(),
                    'view': 'projects',
                    'sellers': sellers,
                    'warning': 'Invalid data. Please correct the errors.'
                })
        except Exception as e:
            print("Error:", e)
            return render(request, 'projects.html', {
                'form': ProjectsForm(),
                'warning': f'Error: {e}'
            })

@login_required
def detail_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id) 
    budgets = BudgetEstimate.objects.filter(project_id=project_id, id_related_budget__isnull=True, isChangeOrder=False)
    invoices = InvoiceProjects.objects.filter(project_id=project_id)
    proposals = ProposalProjects.objects.filter(project_id=project_id)
    changes_orders = BudgetEstimate.objects.filter(project_id=project_id, isChangeOrder=True)
    
    if (len(invoices) <= 0 and len(budgets) <= 0) and project.status not in ['new', 'cancelled', 'inactive', 'pending_payment', 'not_approved']:
        project.status = 'new'
        project.save()
    budgets_with_related = BudgetEstimate.objects.filter(project_id=project_id, id_related_budget__isnull=False, isChangeOrder=False)
    budgets_dict = {}
    for budget in budgets_with_related:
        related_id = budget.id_related_budget.id  # Suponiendo que `id_related_budget` es un atributo accesible
        if related_id not in budgets_dict:
            budgets_dict[related_id] = {'budget': [budget]}
        else:
            budgets_dict[related_id]['budget'].insert(0, budget)
    productionUsers = None  

    if project.status == 'approved':
        groups = Group.objects.prefetch_related("user_set").all()
        admin_users = []
        production_users = []
        for group in groups:
            if group.name == "ADMIN":
                admin_users = [{"name": user.first_name + user.last_name, "email": user.email, "id":  user.id} for user in group.user_set.all()]
            elif group.name == "PRODUCTION":
                production_users = [{"name": user.first_name + user.last_name, "email": user.email, "id":  user.id} for user in group.user_set.all()]
        productionUsers = {'Admins': admin_users, 'Managers':production_users}
    print()
    if project.project_manager and project.status != 'in_production':
        project.status = 'in_production'
        project.save()
        
    if request.method == 'GET':
        status_choices = Project.STATUS_CHOICES
        timeline_steps = get_timeline_steps(project)

    else:
        if 'status' in request.POST:
            new_status = request.POST.get('status') 
            proposal_id = request.POST.get('proposal_id')
            budget_id = request.POST.get('budget_id')
            proposal = get_object_or_404(ProposalProjects, pk=proposal_id)
            budget = get_object_or_404(BudgetEstimate, pk=budget_id)
            if new_status in dict(ProposalProjects.STATUS_CHOICES).keys():
                proposal.status = new_status
                if proposal.status in  ['sent', 'pending'] and budget.status != 'complete':
                    budget.status = 'complete'
                    budget.save()
                elif proposal.status  == 'approved' and budget.status != 'approved':
                    budget.status = 'approved'
                    budget.save()
                elif proposal.status  == 'rejected' and budget.status != 'rejected':
                    budget.status = 'rejected'
                    budget.save()
                elif proposal.status  == 'new' and budget.status != 'saved':
                    budget.status = 'saved'
                    budget.save()
                proposal.save()
                updateStatusProject(new_status, project)
                status_choices = Project.STATUS_CHOICES
                timeline_steps = get_timeline_steps(project)

                
            return render(request, 'details_project.html', {
                'project': project,
                'budgets': budgets,
                'steps': timeline_steps,
                'budgets_dict': budgets_dict,
                'invoices': invoices,
                'proposals':proposals,
                'status_choices': status_choices,
                'productionUsers': productionUsers
            })

    # Renderizar la plantilla
    return render(request, 'details_project.html', {
        'project': project,
        'budgets': budgets,
        'steps': timeline_steps,
        'budgets_dict': budgets_dict,
        'invoices': invoices,
        'proposals':proposals,
        'status_choices': status_choices,
        'changes_orders': changes_orders,
        'productionUsers': productionUsers
    })

@login_required
def select_Manager(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    manager_id = request.GET.get('manager_id')
    user_ids = User.objects.values_list('id', flat=True)
    print(list(user_ids))
    print(manager_id)
    manager = get_object_or_404(User, id=manager_id)
    project.project_manager = manager
    project.status = 'in_production'
    project.save()
    if manager_id:
        print(f"Manager selected: {manager_id}")
    
    return redirect('detail_project', project_id)


@login_required    
def new_budget(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'GET':
        return render(request, 'new_budget.html', {
            'project': project,
            'date': date.today(),
            'date_valid' : date.today() + timedelta(days=25),
        })
    else:
        try:
            data = json.loads(request.body)
            print('Datos recibidos',data)
            dataBudget = {
                'project': project, 
                'projectedCost': data['utilsData']['costTotal'], 
                'profitValue': data['utilsData']['profitTotal'],
                'actualCost':0, 
                'status': BudgetEstimate.STATUS_SAVED,
                'sales': request.user, 
                'dateCreated': timezone.now(),  
            }
            save_budget_data_from_dict(dataBudget, data)
            return JsonResponse({'status': 'success', 'message': 'Presupuesto y datos guardados correctamente.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al procesar los datos.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al guardar el presupuesto: {str(e)}'}, status=500)
    
@login_required
def view_changeOrder(request, project_id,  budget_id):
    project = get_object_or_404(Project, pk=project_id)
    budget = get_object_or_404(BudgetEstimate, pk=budget_id)
    qtCHO = BudgetEstimate.objects.filter(id_related_budget=budget.id_related_budget, isChangeOrder=True)
    if request.method == 'GET':
        return render(request, 'view_changeOrder.html', {
            'project': project,
            'budget': budget,
            'qtChangeOrder': len(qtCHO),
        })


def view_budget(request, project_id, budget_id): 
    project = get_object_or_404(Project, pk=project_id)
    budget = get_object_or_404(BudgetEstimate, pk=budget_id)
    
    if request.method == 'GET':
        data = extract_data_budget(budget)
        print(data)
        return render(request, 'view_budget.html', {
            'project': project,
            'budget': budget,
            'date': date.today(),
            'date_valid' : date.today() + timedelta(days=25),
            'data':  json.dumps(data)
        })
            
@login_required 
def new_change_order(request, project_id, proposal_id):
    project = get_object_or_404(Project, pk=project_id)
   
    if request.method == 'GET':
        proposal = get_object_or_404(ProposalProjects, pk=proposal_id)
        budget = proposal.budget
        data = extract_data_budget(budget)
        return render(request, 'new_changeOrder.html', {
            'project': project,
            'budget': budget,
            'date': date.today(),
            'date_valid' : date.today() + timedelta(days=25),
            'data':  json.dumps(data)
        })
    else:
        try:
            budget = get_object_or_404(BudgetEstimate, pk=proposal_id)
            data = json.loads(request.body)
            budgetRelated = budget
            dataBudget = {
                'project': project, 
                'projectedCost': data['utilsData']['costTotal'], 
                'profitValue': data['utilsData']['profitTotal'],
                'actualCost':0, 
                'status': BudgetEstimate.STATUS_SAVED,
                'sales': request.user, 
                'dateCreated': timezone.now(),  
                'related_budget':budgetRelated, 
                'isChangeOrder': True,
            }
            save_budget_data_from_dict(dataBudget, data)
            return JsonResponse({'status': 'success', 'message': 'Orden de cambio guardada correctamente.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al procesar los datos.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al guardar la orden de cambio: {str(e)}'}, status=500)

@login_required 
def edit_budget(request, project_id, budget_id):
    project = get_object_or_404(Project, pk=project_id)
    budget = get_object_or_404(BudgetEstimate, pk=budget_id)
    budgetRelated = budget.id_related_budget
    if request.method == 'GET':
        data = extract_data_budget(budget)
        print(data)
        return render(request, 'edit_budget.html', {
            'project': project,
            'budget': budget,
            'date': date.today(),
            'date_valid' : date.today() + timedelta(days=25),
            'data':  json.dumps(data)
        })
    else:
        try:
            data = json.loads(request.body)
            
            if not budgetRelated:
                budgetRelated = budget
                
            dataBudget = {
                'project': project, 
                'projectedCost': data['utilsData']['costTotal'], 
                'profitValue': data['utilsData']['profitTotal'],
                'actualCost':0, 
                'status': BudgetEstimate.STATUS_SAVED,
                'sales': request.user, 
                'dateCreated': timezone.now(),  
                'related_budget':budgetRelated, 
            }
            save_budget_data_from_dict(dataBudget, data)
            modify_old_budget(budget_id)
            return JsonResponse({'status': 'success', 'message': 'Presupuesto actualizado correctamente.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al procesar los datos.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al actualizar el presupuesto: {str(e)}'}, status=500)

def generate_pdf(request, project_id, budget_id):
    """context = get_budget_context(project_id, budget_id)

        # Renderizar la plantilla HTML como una cadena
        html_string = render_to_string('project/budget_template.html', context)

        # Crear un archivo PDF temporal
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="budget_report.pdf"'

        # Usar WeasyPrint para generar el PDF
        HTML(string=html_string).write_pdf(response)"""

    pass

@login_required 
def view_budgetSimple(request, project_id, budget_id):
    project = get_object_or_404(Project, pk=project_id)
    budget = get_object_or_404(BudgetEstimate, pk=budget_id)

    if request.method == 'POST':
        data = request.POST
        dictScope = {}
        id = None
        for key, value in data.items():
            if 'scope' in  key:
                id = key.split('-')[1]
                dictScope[id]= {}
                dictScope[id]['scope']=[data[key]]
            if 'materials' in  key:
                dictScope[id]['materials']=[data[key]]
        saleAdvisor = request.user
        save_budget_simple(data, project, budget, dictScope,saleAdvisor)

            
        return redirect('detail_project', project_id=project_id)

    else:
        return render(request, 'view_budgetSimpleSend.html',{   'budget':budget, 
                                                                'project': project, 
                                                                'now': timezone.now(), 
                                                                })

@login_required 
def delete_budget(request, project_id, budget_id):
    budget = get_object_or_404(BudgetEstimate, id=budget_id)
    budget.delete()
    
    return redirect('detail_project', project_id=project_id)

@login_required
def delete_project(request, project_id, folder_root_value=None):
    project = get_object_or_404(Project, pk=project_id)
    if folder_root_value:
        delete_folder_response = delete_folders_by_projects(project.project_name, folder_root_value)
        print(delete_folder_response)
        project.delete()
        return redirect('projects')
    else:
        project.delete()
        return redirect('projects')
    
@login_required
def delete_invoice(request, project_id, invoice_id):
    """
    Deletes an invoice and updates the related project's estimated cost 
    and budget's status accordingly.

    Args:
        request: The HTTP request object.
        project_id (int): The ID of the project to which the invoice belongs.
        invoice_id (int): The ID of the invoice to delete.

    Returns:
        HttpResponseRedirect: Redirects to the project detail view after deletion.
    """
    with transaction.atomic():
        invoice = get_object_or_404(InvoiceProjects, id=invoice_id)
        invoice.delete()

    return redirect('detail_project', project_id=project_id)

@login_required
def delete_proposal(request, project_id, proposal_id):
    """
    Deletes an proposal and updates the related project's estimated cost 
    and budget's status accordingly.

    Args:
        request: The HTTP request object.
        project_id (int): The ID of the project to which the proposal belongs.
        proposal_id (int): The ID of the proposal to delete.

    Returns:
        HttpResponseRedirect: Redirects to the project detail view after deletion.
    """
    with transaction.atomic():
        proposal = get_object_or_404(ProposalProjects, id=proposal_id)
        budget = proposal.budget
        project = get_object_or_404(Project, id=project_id)
        project.estimated_cost = F('estimated_cost') - proposal.total_proposal
        project.save(update_fields=['estimated_cost'])
        proposal.delete()
        # percentage_of_budget = budget.total_percentage_proposald
        # if percentage_of_budget >= 99:
        #     budget.status = 'Complete'
        # elif percentage_of_budget == 0:
        #     budget.status = 'New'
        # else:
        #     budget.status = 'Billed'
        budget.save(update_fields=['status'])

    return redirect('detail_project', project_id=project_id)

def pdf_invoice(request, project_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    invoice = get_object_or_404(InvoiceProjects, id=invoice_id)

    if request.method == 'GET':
        return render(request, 'pdf_invoice.html', {
            'project': project,
            'invoice':invoice})
    elif request.method == 'POST':
        return HttpResponse(status=200)
    
def pdf_proposal(request, project_id, proposal_id):
    project = get_object_or_404(Project, pk=project_id)
    proposal = get_object_or_404(ProposalProjects, id=proposal_id)

    if request.method == 'GET':
        return render(request, 'pdf_proposal.html', {
            'project': project,
            'proposal':proposal})
    elif request.method == 'POST':
        return HttpResponse(status=200)
    
@transaction.atomic
def save_budget_data_from_dict(dataBudget,data):
    """
    Crea un nuevo BudgetEstimate y guarda los datos relacionados a partir de un diccionario.
    :param data: Diccionario con los datos a guardar.
    :return: El objeto BudgetEstimate creado
    """
    try:
        related_budget = None
        if dataBudget.get('related_budget'):
            related_budget = dataBudget.get('related_budget')  # Ajusta esto si necesitas buscar un objeto relacionado
        if dataBudget.get('isChangeOrder'):
            isChangeOrder = True
        else:
            isChangeOrder = False
        # Crea el presupuesto
        budget = BudgetEstimate.objects.create(
            project=dataBudget.get('project'),
            projected_cost=dataBudget.get('projectedCost'),
            profit_value=dataBudget.get('profitValue'),  
            actual_cost=dataBudget.get('actualCost'),  
            status=dataBudget.get('status'),
            sales_advisor=dataBudget.get('sales'),  
            date_created=dataBudget.get('dateCreated'),
            id_related_budget=related_budget,
            isChangeOrder=isChangeOrder, 
            dataPreview=data.get('tableCostData'),
        )
        
        # Guardar datos de Utilidad (dataHolePosts)
        if 'utilsData' in data:
            util_data =  data['utilsData']
            
            util_data_hole = util_data['dataHolePosts']
            util_data_MI = util_data['dataUnitCostMi']
            util_data_MW = util_data['dataUnitCostMW']
            util_data_Pday = util_data['dataProfitByDay']
            util_data_loans = util_data['dataLoans']
            BudgetEstimateUtil.objects.create(
                budget=budget,
                add_post_and_hole = util_data_hole.get('addTotalFtPosts'),
                add_hole_checked=util_data_hole.get('addHoleChecked'),
                add_utilities_checked=util_data_hole.get('addUtilitiesChecked'),
                add_removal_checked=util_data_hole.get('addRemovalChecked'),
                totalFtAdPost=util_data_hole.get('totalFtAdPost'),
                hole_cost=util_data_hole.get('holeCost'),
                cost_per_hole=util_data_hole.get('costPerHole'),
                utilities_cost=util_data_hole.get('utilitiesCost'),
                removal_cost=util_data_hole.get('removalCost'),
                ############
                add_unit_cost_mi = util_data_MI.get('addUnitCostMi'),
                manufacturing_data = util_data_MI.get('manufacturingData'),
                cost_data = util_data_MI.get('costData'),
                profit_value_installation_check = util_data_MI.get('profitValueInstallationCheck'),
                profit_value_installation = util_data_MI.get('profitValueInstallation'),
                #####
                add_unit_cost_mw = util_data_MW.get('addUnitCostMW'),
                data_unit_cost_mw = util_data_MW.get('dataUnitCostMWCost'),
                data_unit_cost_mw_items = util_data_MW.get('dataUnitCostMWItems'),
                add_data_profit_by_daymw =  util_data_MW.get('adddataProfitByDayMW'),
                data_profit_by_daymw =  util_data_MW.get('valueProfitByDayMW'),
                #####
                add_data_profit_by_day =  util_data_Pday.get('adddataProfitByDay'),
                days = util_data_Pday.get('dataProfitByDay', {}).get('days', 0),
                profit_value = util_data_Pday.get('dataProfitByDay', {}).get('profitValue', 0),
                use_day_in_items_manufacturing = util_data_Pday.get('dataProfitByDay', {}).get('useDayInItemsManufacturing', False),
                ####
                # Información de préstamos
                add_loans = util_data_loans.get('addLoans'),
                percentage = util_data_loans.get('dataLoansToProject', {}).get('percentage', 0),
                margin_error_check = util_data.get('checkMarginError'),
                percentage_margin_error = util_data.get('percentageMarginError'),
            )
            
            
        if 'laborData' in data:
            laborData = data['laborData']   
            for labor in laborData:
                BudgetEstimateLaborData.objects.create(
                    budget=budget,
                    labor_description=labor['laborDescription'],
                    cost_by_day=labor['costByDay'],
                    days=labor['days'],
                    lead_time=labor['leadTime'],
                    labor_cost=labor['laborCost'],
                    item_value=labor.get('itemValue'),
                    is_generated_by_utils=labor['isGeneratedByUtils']
                )
        if 'materialsData' in data:
            materials_data = data['materialsData']
            for material in materials_data:
                BudgetEstimateMaterialData.objects.create(
                    budget=budget,
                    material_description=material.get('materialDescription'),
                    quantity=material.get('quantity'),
                    unit_cost=material.get('unitCost'),
                    lead_time=material.get('leadTime'),
                    cost=material.get('cost'),
                    item_value=material.get('itemValue'),
                    is_generated_by_utils=material.get('isGeneratedByUtils'),
                    is_generated_by_checklist=material.get('isGeneratedByCheckList'),
                    id_generated_by_checklist=material.get('idGeneratedByCheckList'),
                )
        if 'contractorData' in data:
            contractor_data = data['contractorData']     
            for contractor in contractor_data:
                BudgetEstimateContractorData.objects.create(
                    budget=budget,
                    contractor_description=contractor.get('contractorDescription'),
                    lead_time=contractor.get('leadTime'),
                    contractor_cost=contractor.get('contractorCost'),
                    item_value=contractor.get('itemValue'),
                    is_generated_by_utils=contractor.get('isGeneratedByUtils'),
                )
        if 'miscData' in data:
            misc_data =  data['miscData']   
            for misc in misc_data:
                BudgetEstimateMiscData.objects.create(
                    budget=budget,
                    misc_description=misc.get('description'),
                    misc_value=misc.get('miscCost'),
                    item_value=misc.get('itemValue'),
                    lead_time=misc.get('leadTime'),
                    is_generated_by_utils=misc.get('isGeneratedByUtils'),
                )
        if 'deductsData' in data:
            deducts_data =  data['deductsData']   
            for deduct in deducts_data:
                BudgetEstimateDeductsData.objects.create(
                    budget=budget,
                    deduct_description=deduct.get('description'),
                    deduct_value=deduct.get('unitCost'),
                    item_value=deduct.get('itemValue'),
                    lead_time=deduct.get('leadTime'),
                    is_generated_by_utils=deduct.get('isGeneratedByUtils'),
                )
        if 'profitData' in data:
            profit_data =  data['profitData']   
            for profit in profit_data:
                BudgetEstimateProfitData.objects.create(
                    budget=budget,
                    profit_description=profit.get('profitDescription'),
                    lead_time=profit.get('leadTime'),
                    profit_value=profit.get('profitValue'),
                    item_value=profit.get('itemValue'),
                    is_generated_by_utils=profit.get('isGeneratedByUtils'),
                )
        
        print({'status': 'success', 'message': 'Presupuesto y datos guardados correctamente.', 'budget_id': budget.id})
        return budget
    except Exception as e:
        print({'status': 'error', 'message': str(e)})
        raise


def save_budget_simple(data, project, budget, dictScope, saleAdvisor):
    with transaction.atomic():
        # Recolectar los precios por scope
        scope_prices = {}
        for key, value in data.items():
            if key.startswith('scope-price-'):
                scope_id = key.replace('scope-price-', '')
                if value:  # Solo guardar si hay un valor
                    scope_prices[scope_id] = float(value.replace('$', '').replace(',', ''))

        proposal = ProposalProjects.objects.create(
            project=project,
            budget=budget,
            tracking_id='',
            proposalInfo=dictScope,
            date_created=data['date_created'],
            project_name=data['project_name'],
            due_date=data['valid_until'],
            subtotal=data['subtotal'],
            tax=data['tax'],
            retention=data['retention'],
            total_proposal=float(data['subtotal']) + float(data['tax']) - float(data['retention']),
            approved_by=data['approved_by'],
            print_name=data['print_name'],
            signature=data['signature'],
            sales_advisor=saleAdvisor,
            terms_conditions=data['terms'],
            exclusions=data.get('exclusions', 'Permit Fee and processing, Site survey, Electrical fence grounding'),
            scope_prices=scope_prices,  # Guardar los precios por scope
        )
        project.estimated_cost = F('estimated_cost') + proposal.total_proposal
        project.save(update_fields=['status', 'estimated_cost'])

    
def modify_old_budget(budget_id):
    budget = BudgetEstimate.objects.get(id=budget_id)
    budget.mark_as_obsolete()


def extract_data_budget(budget):
    data = {
        "labors": list( budget.labors.values(
            'id', 'labor_description', 'cost_by_day', 'days', 'lead_time', 'labor_cost', 'item_value', 'is_generated_by_utils'
        )),
        "materials": list(budget.materials.values(
            'id', 'material_description', 'quantity', 'unit_cost', 'lead_time', 'cost', 'item_value', 'is_generated_by_utils', 'id_generated_by_checklist', 'is_generated_by_checklist'
        )),
        "contractors": list(budget.contractors.values(
            'id', 'contractor_description', 'lead_time', 'contractor_cost', 'item_value', 'is_generated_by_utils'
        )),
        "misc_data": list(budget.misc_data.values(
            'id', 'misc_description', 'misc_value', 'lead_time', 'item_value', 'is_generated_by_utils'
        )),
        "deducts": list(budget.deducts.values(
            'id', 'deduct_description', 'deduct_value', 'lead_time', 'item_value', 'is_generated_by_utils'
        )),
        "profits": list(budget.profits.values(
            'id', 'profit_description', 'lead_time', 'profit_value', 'item_value', 'is_generated_by_utils'
        )),
        "utils": list(budget.util_data.values(
            'id', 'add_hole_checked', 'add_utilities_checked', 'add_removal_checked',
            'totalFtAdPost', 'hole_cost', 'cost_per_hole', 'profit_value_installation_check', 'profit_value_installation',
            'utilities_cost', 'removal_cost', 'add_unit_cost_mi', 'add_unit_cost_mw', 'manufacturing_data',
            'cost_data', 'data_unit_cost_mw', 'data_unit_cost_mw_items', 'add_data_profit_by_daymw','data_profit_by_daymw', 'add_data_profit_by_day','add_post_and_hole',
            'days', 'profit_value', 'use_day_in_items_manufacturing', 'add_loans', 'percentage', 'margin_error_check', 'percentage_margin_error'
        )),}
    serialized_data = decimal_to_float(data)
    return serialized_data

def decimal_to_float(data):
    """
    Convierte valores Decimal en el contexto para que sean JSON serializables.
    """
    if isinstance(data, list):
        return [decimal_to_float(item) for item in data]
    elif isinstance(data, dict):
        return {key: decimal_to_float(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return float(data)  # O str(data) si prefieres
    else:
        return data
    
def save_invoice(data,project, budget, proposal, saleAdvisor):
    if data['startDate']:
        date_created = datetime.strptime(data['startDate'], '%Y-%m-%d')
    else:
        date_created = datetime.strptime(data['dateId'], '%Y-%m-%d')
        
    if data['endDate']:
        due_date = data['endDate']
    else:
        due_date = date_created + timedelta(days=90)
    
    with transaction.atomic():
        invoice = InvoiceProjects.objects.create(
            project=project,
            budget=budget,
            proposal=proposal,
            invoiceInfo=data,
            date_created=date_created,
            due_date = due_date,
            total_invoice=float(data['total']),
            sales_advisor=saleAdvisor,
            type_invoice=data['type']
        )
    
    
               
        
@receiver(post_save, sender=InvoiceProjects)
@receiver(post_delete, sender=InvoiceProjects)
def update_billed_proposal(sender, instance, **kwargs):
    proposal = instance.proposal
    total_billed = proposal.invoices.aggregate(total=Sum('total_invoice'))['total'] or 0
    proposal.billed_proposal = total_billed
    proposal.save()
    

def updateStatusProject(proposalStatus, project):
    print('algo')
    if proposalStatus == 'sent' and project.status != 'contacted':
        project.status = 'contacted'
        project.save()
    elif  proposalStatus == 'pending' and project.status != 'quote_sent':
        project.status = 'quote_sent'
        project.save()
    elif  proposalStatus == 'approved' and project.status != 'approved':
        project.status = 'approved'
        project.save()

@login_required
def chat_with_groq(request):
    if request.method == "POST":
        dataPromt = json.loads(request.body)
        user_message =dataPromt.get("message", "")
        context_message =dataPromt.get("messageHistory", "")
        context_message =dataPromt.get("messageHistory", "")
        typeMessage =dataPromt.get("type", "")
        typeTable=dataPromt.get("table", "")
        if typeMessage == 'consulta':
            promt = basePromt.replace('{user_question}', user_message)
            promt = promt.replace('{table}', typeTable)
        else:
            promt = AsisPromt.replace('{user_question}', user_message)
        promt = promt.replace('{user_id}', str(request.user.id))
        promt = promt.replace('{user_name}', str(request.user))
        if context_message:
            promt = promt.replace('{context}', str(context_message))
        if not user_message:
            return JsonResponse({"error": "No message provided"}, status=400)
        try:
            chat_completion = client.chat.completions.create(
            messages=[
                {
                "role": "system",
                "content": "you are a helpful assistant. Your responses should always be in json that have a type, content, model, table. Remember that the output must always be in this format: {\"type\": \"consulta\", \"content\": \"SELECT * FROM customer_project WHERE is_active = TRUE LIMIT 5;\", \"model\": \"BudgetEstimate\", \"table\": \"customer_invoiceprojects\"}"
                },
                {"role": "user",
                "content": promt,
                }
            ],
            stream=False,
            response_format={"type": "json_object"},
            model="deepseek-r1-distill-llama-70b",)
            response_message = Recipe.model_validate_json(chat_completion.choices[0].message.content)
            data = response_message
            print(data)
            # Extraer la respuesta del modelo
            if data.type == 'consulta':
                result = QueryIA(data.content, data.table, data.model)
                analisys = ReviewAnalisisIA(result, data.table, context_message).model_dump()
                return JsonResponse({"response": analisys})
            else:
                response_message = RecipeGeneral.model_validate_json(chat_completion.choices[0].message.content)
                return JsonResponse({"response": data.content}) 
        except Exception as e:
            return JsonResponse({"Puedes reformular tu pregunta por favor!!"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)



def QueryIA(query, table_name, model_name):
    try:
        print(f"Query recibido: {query}")
        model = apps.get_model('customer', model_name)
        print(f"Modelo obtenido: {model}")
        try:
            result = model.objects.raw(query)
            print("Resultado obtenido:")
            json_data = serialize("json", list(result))
        except:
            print("Arreglando el Query")
            query = ReviewQueryIA(query,model)
            result = model.objects.raw(query)
            print("Resultado obtenido:")
            json_data = serialize("json", list(result))
       
        print("Datos serializados en JSON:")
        return json_data
    except Exception as e:
        print("Ocurrió un error:")
        traceback.print_exc()
        return {"error": 'Lo Lamento actualmente no cuento con sufiencientes datos para hacer consultas, solo te puedo asistir'}

    
def ReviewQueryIA(query, model):
    nameModel = model.__name__
    promt = QueryReviewPrompt(nameModel, query)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": promt,
                }
            ],
            model="deepseek-r1-distill-llama-70b",
        )
        response_message = chat_completion.choices[0].message.content
        matches =  response_message.split('</think>')
        pattern = r"#\s*(.*?)\s*#"
        match = re.search(pattern, matches[-1], re.DOTALL)
        print(match)
        return match.group(1) 
    except Exception as e:
        return JsonResponse({"error": 'Lo Lamento actualmente no cuento con sufiencientes datos para hacer consultas, solo te puedo asistir'}, status=400)
    
    
def ReviewAnalisisIA(json, model, context):
    if context:
        response_data = analisys.model_dump()
        promt = AnalysiData.replace('{context}', str(context))
        promt = promt.replace('{json_data}', json)
    else:
        promt = promt.replace('{json_data}', json)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                "role": "system",
                "content": "you are a helpful assistant." + SystemPromtReviewData
                },
                {"role": "user",
                "content": promt,
                }
            ],
            stream=False,
            response_format={"type": "json_object"},
            model="deepseek-r1-distill-llama-70b",
        )
        response_message = RecipeAnalysis.model_validate_json(chat_completion.choices[0].message.content)
        print(response_message)
        return response_message
    except Exception as e:
        return JsonResponse({"error": 'Lo Lamento actualmente no cuento con sufiencientes datos para hacer consultas, solo te puedo asistir'}, status=400)
    
    
def ReviewModelIA(query, table_model):
    models = apps.get_models()
    for model in models:
        print(model.__name__)
    promt = AnalysiData(table_model, query)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user",
                "content": promt,
                }
            ],
            model="deepseek-r1-distill-llama-70b",
        )
        response_message = chat_completion.choices[0].message.content
    except Exception as e:
        return JsonResponse({"error": 'Lo Lamento actualmente no cuento con sufiencientes datos para hacer consultas, solo te puedo asistir'}, status=400)
    


class Recipe(BaseModel):
    type: str
    content: str
    model: Optional[str]
    table: Optional[str]
    
class RecipeGeneral(BaseModel):
    type: str
    content: str

class KeyData(BaseModel):
    tittle: str
    review: str
class RecipeAnalysis(BaseModel):
    type: str
    table: str
    href: str
    resumen: str
    key_data: List[KeyData]
    observations: List[str]
    
def JsonTableAnalisyModelIA(json, context):
    promt = AnalysiData.replace('{context}', str(context))
    promt = promt.replace('{json_data}', str(json))
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                "role": "system",
                "content": "you are a helpful assistant."
                },
                {"role": "user",
                "content": promt,
                }
            ],
            stream=False,
            response_format={"type": "json_object"},
            model="deepseek-r1-distill-llama-70b",
        )
        response_message = Recipe.model_validate_json(chat_completion.choices[0].message.content)
        matches =  response_message.split('</think>')
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, matches[-1], re.DOTALL)
        if match:
            return match
        return response_message    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def project_history(request, project_id):
    """
    Vista para mostrar el historial de cambios de un proyecto.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Obtener el historial del proyecto
    history_entries = ProjectHistory.objects.filter(project=project).order_by('-timestamp')
    
    # Paginar los resultados
    paginator = Paginator(history_entries, 20)  # 20 entradas por página
    page = request.GET.get('page')
    history = paginator.get_page(page)
    
    context = {
        'project': project,
        'history': history,
    }
    
    return render(request, 'project_history.html', context)
