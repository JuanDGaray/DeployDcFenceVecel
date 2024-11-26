from re import I
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import (Customer, Project, User,
                      BudgetEstimate, BudgetEstimateMaterialData, BudgetEstimateDeductsData,
                      BudgetEstimateLaborData, BudgetEstimateContractorData,
                      BudgetEstimateMiscData, BudgetEstimateProfitData, BudgetEstimateUtil, InvoiceProjects)

from ..form import CustomerForm, ProjectsForm  # Ensure the correct import for the form
from django.core.paginator import Paginator
from django.utils.text import capfirst
from decimal import Decimal
from django.db.models import Sum
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from datetime import date, timedelta
from django.utils import timezone
import json
import math


def get_timeline_steps(project):
    status_choices = Project.STATUS_CHOICES
    current_status_index = next(index for index, (status, _) in enumerate(status_choices) if status == project.status)
    
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
    # Retrieve all projects and paginate them
    Project_list = Project.objects.all()
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


def detail_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    budgets = BudgetEstimate.objects.filter(project_id=project_id, id_related_budget__isnull=True)
    invoices = InvoiceProjects.objects.filter(project_id=project_id)
    print(invoices,  project.status)
    if (len(invoices) <=0  or len(budgets)) <=0 and project.status not in ['new', 'cancelled', 'inactive', 'pending_payment', 'not_approved']:
        project.status = 'new'
        project.save()
    
    budgets_with_related = BudgetEstimate.objects.filter(project_id=project_id, id_related_budget__isnull=False)

    # Prepare budgets dict with relevant data for the template
    budgets_dict = {}
    for budget in budgets_with_related:
        related_id = budget.id_related_budget.id  # suponer que `id_related_budget` es un atributo accesible
        if related_id not in budgets_dict:
            budgets_dict[related_id] = {'budget': [budget]}
        else:
            budgets_dict[related_id]['budget'].insert(0, budget)

    
    status_choices = Project.STATUS_CHOICES
    timeline_steps = get_timeline_steps(project)

    return render(request, 'details_project.html', {
        'project': project,
        'budgets': budgets,
        'steps': timeline_steps,
        'budgets_dict': budgets_dict,
        'invoices':invoices,
    })


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
            print(data)
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
            return redirect('detail_project', project_id=project.id)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al procesar los datos.'})
    

        


@login_required 
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
def edit_budget(request, project_id, budget_id):
    project = get_object_or_404(Project, pk=project_id)
    budget = get_object_or_404(BudgetEstimate, pk=budget_id)
    
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
            if data['primaryBudget']:
                budgetRelated = get_object_or_404(BudgetEstimate, pk=data['primaryBudget'])
            else:
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
            return redirect('detail_project', project_id=project.id)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al procesar los datos.'})


@login_required 
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
def delete_invoice(request, project_id, invoice_id):
    print('invoice', invoice_id)
    invoice = get_object_or_404(InvoiceProjects, id=invoice_id)
    budget = invoice.budget
    invoice.delete()
    percentage_of_budget = budget.total_percentage_invoiced
    if percentage_of_budget >= 99:
        budget.status = 'Complete'
    elif percentage_of_budget == 0:
        budget.status = 'New'
    else:
        budget.status = 'Billed'
    budget.save()
    return redirect('detail_project', project_id=project_id)


def save_budget_data_from_dict(dataBudget,data):
    """
    Crea un nuevo BudgetEstimate y guarda los datos relacionados a partir de un diccionario.
    :param data: Diccionario con los datos a guardar.
    """
    try:
        # Crear una nueva instancia de BudgetEstimate
        related_budget = None
        if dataBudget.get('related_budget'):
            related_budget = dataBudget.get('related_budget')  # Ajusta esto si necesitas buscar un objeto relacionado

        # Crea el presupuesto
        budget = BudgetEstimate.objects.create(
            project=dataBudget.get('project'),
            projected_cost=dataBudget.get('projectedCost'),
            profit_value=dataBudget.get('profitValue'),  
            actual_cost=dataBudget.get('actualCost'),  
            status=dataBudget.get('status'),
            sales_advisor=dataBudget.get('sales'),  
            date_created=dataBudget.get('dateCreated'),
            id_related_budget=related_budget
        )
        
        # Guardar datos de Utilidad (dataHolePosts)
        if 'utilsData' in data:
            util_data =  data['utilsData']
            
            util_data_hole = util_data['dataHolePosts']
            util_data_MI = util_data['dataUnitCostMi']
            util_data_MW = util_data['dataUnitCostMW']
            util_data_Pday = util_data['dataProfitByDay']
            util_data_loans = util_data['dataLoans']
            print(util_data_MW['adddataProfitByDayMW'])
            BudgetEstimateUtil.objects.create(
                budget=budget,
                add_hole_checked=util_data_hole.get('addHoleChecked'),
                add_utilities_checked=util_data_hole.get('addUtilitiesChecked'),
                add_removal_checked=util_data_hole.get('addRemovalChecked'),
                total_ft=util_data_hole.get('totalFt'),
                total_posts=util_data_hole.get('totalPosts'),
                hole_quantity=util_data_hole.get('holeQuantity'),
                hole_cost=util_data_hole.get('holeCost'),
                cost_per_hole=util_data_hole.get('costPerHole'),
                utilities_cost=util_data_hole.get('utilitiesCost'),
                removal_cost=util_data_hole.get('removalCost'),
                ############
                add_unit_cost_mi = util_data_MI.get('addUnitCostMi'),
                manufacturing_data = util_data_MI.get('manufacturingData'),
                cost_data = util_data_MI.get('costData'),
                #####
                add_unit_cost_mw = util_data_MW.get('addUnitCostMW'),
                data_unit_cost_mw = util_data_MW.get('dataUnitCostMWCost'),
                data_unit_cost_mw_items = util_data_MW.get('dataUnitCostMWItems'),
                add_data_profit_by_daymw =  util_data_MW['adddataProfitByDayMW'],
                data_profit_by_daymw =  util_data_MW['valueProfitByDayMW'],
                #####
                add_data_profit_by_day =  util_data_Pday.get('adddataProfitByDay'),
                days = util_data_Pday['dataProfitByDay']['days'],
                profit_value = util_data_Pday['dataProfitByDay']['profitValue'],
                use_day_in_items_manufacturing = util_data_Pday['dataProfitByDay']['useDayInItemsManufacturing'],
                ####
                # Información de préstamos
                add_loans = util_data_loans.get('addLoans'),
                percentage = util_data_loans['dataLoansToProject']['percentage'],
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
    except Exception as e:
        print({'status': 'error', 'message': str(e)})


def save_budget_simple(data, project, budget, dictScope, saleAdvisor):
    invoice = InvoiceProjects.objects.create(
    project = project,
    budget = budget,
    tracking_id =  data['tracking'],
    invoiceInfo = dictScope,
    date_created = data['date_created'],
    project_name=data['project_name'],
    due_date=data['valid_until'],
    subtotal=data['subtotal'],
    tax=data['tax'],
    retention=data['retention'],
    total_invoice= int(float(data['subtotal']) + float(data['tax']) - float(data['retention'])),
    approved_by=data['approved_by'],
    print_name=data['print_name'],
    signature=data['signature'],
    sales_advisor = saleAdvisor,
    terms_conditions = data['terms'],
    )
    percentage_of_budget = budget.total_percentage_invoiced
    if percentage_of_budget >= 99:
        budget.status = 'Complete'
    else:
        budget.status = 'Billed'
    budget.save()
    if project.status in ['new']:
        project.status = 'contacted'
        project.save()
def modify_old_budget(budget_id):
    budget = BudgetEstimate.objects.get(id=budget_id)
    budget.mark_as_obsolete()



def extract_data_budget(budget):
    data = {
        "labors": list( budget.labors.values(
            'id', 'labor_description', 'cost_by_day', 'days', 'lead_time', 'labor_cost', 'item_value', 'is_generated_by_utils'
        )),
        "materials": list(budget.materials.values(
            'id', 'material_description', 'quantity', 'unit_cost', 'lead_time', 'cost', 'item_value', 'is_generated_by_utils'
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
            'total_ft', 'total_posts', 'hole_quantity', 'hole_cost', 'cost_per_hole',
            'utilities_cost', 'removal_cost', 'add_unit_cost_mi', 'manufacturing_data',
            'cost_data', 'data_unit_cost_mw', 'data_unit_cost_mw_items', 'add_data_profit_by_daymw','data_profit_by_daymw', 'add_data_profit_by_day',
            'days', 'profit_value', 'use_day_in_items_manufacturing', 'add_loans', 'percentage'
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