from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from ..models import Customer, Project
from datetime import datetime

def search_customers(request):
    name = request.GET.get('name', '')
    company = request.GET.get('company', '')
    email = request.GET.get('email', '')
    seller = request.GET.get('seller', '')
    date = request.GET.get('date', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)  # Tomar el número de página de la petición

    filters = Q()
    if name:
        filters &= Q(first_name__icontains=name) | Q(last_name__icontains=name)
    if company:
        filters &= Q(company_name__icontains=company)
    if email:
        filters &= Q(email__icontains=email)
    if seller:
        filters &= Q(sales_advisor__username__icontains=seller)
    if status:
        filters &= Q(status__icontains=status)
        print("yes")
    if date:
        try:
            filters &= Q(date_created__date=date)
        except ValueError:
            filters &= Q(id__isnull=True)

    customers = Customer.objects.filter(filters)

    # Paginar los resultados
    paginator = Paginator(customers, 20)  # Mostrar 20 clientes por página
    page_obj = paginator.get_page(page)

    # Preparar datos para la respuesta JSON
    data = [
        {
            'id': customer.id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'company_name': customer.company_name,
            'customer_type': customer.customer_type,
            'email': customer.email,
            'phone': customer.phone,
            'project': customer.id,
            'status': customer.status,
            'date_created': customer.date_created.strftime('%d/%m/%Y'),
            'sales_advisor': customer.sales_advisor.username,
        } for customer in page_obj
    ]

    # Enviar datos de paginación también
    response = {
        'customers': data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages
    }

    return JsonResponse(response)


def search_projects(request):
    print(request)
    project_id = request.GET.get('id', '')
    project_name = request.GET.get('project_name', '')
    status = request.GET.get('status', '')
    customer = request.GET.get('customer', '')
    seller = request.GET.get('seller', '')
    date = request.GET.get('date', '')
    page = request.GET.get('page', 1)  # Página actual

    filters = Q()
    if project_id:
        filters &= Q(id=project_id)
    if project_name:
        filters &= Q(project_name__icontains=project_name)
    if status:
        filters &= Q(status__icontains=status)
    if customer:
        filters &= (
            Q(customer__first_name__icontains=customer) |
            Q(customer__last_name__icontains=customer) |
            Q(customer__email__icontains=customer)
        )
    if seller:
        filters &= Q(sales_advisor__username__icontains=seller)
    if date:
        try:
            # Intentar convertir el string a formato de fecha
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            filters &= Q(date_created__date=date_obj)
        except ValueError:
            filters &= Q(id__isnull=True)  # Filtro que no devuelve resultados si la fecha no es válida

    # Filtrar los proyectos basados en los filtros aplicados
    projects = Project.objects.filter(filters).select_related('customer', 'sales_advisor')

    # Paginar los resultados
    paginator = Paginator(projects, 20)  # Mostrar 20 proyectos por página
    page_obj = paginator.get_page(page)

    # Preparar datos para la respuesta JSON
    data = [
        {
            'id': project.id,
            'created_at': project.created_at.strftime('%d/%m/%Y'),
            'project_name': project.project_name,
            'status': project.status,
            'customer_type': project.customer.customer_type,
            'customer_first_name': project.customer.first_name,
            'customer_last_name': project.customer.last_name,
            'customer_company_name': project.customer.company_name,
            'customer_id': project.customer.id,
            'estimated_budget': project.estimated_cost,
            'actual_budget': project.actual_cost,
            'sales_advisor': project.sales_advisor.username,
        } for project in page_obj
    ]

    # Enviar datos de paginación también
    response = {
        'projects': data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages
    }

    return JsonResponse(response)


def check_email_exists(request):
    email = request.GET.get('email')
    exists = Customer.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})