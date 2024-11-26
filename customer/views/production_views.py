from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Customer, Project, User
from ..form import CustomerForm 
from django.core.paginator import Paginator


@login_required
def production(request):
    # Retrieves the list of all customers and paginates it
    Project_list = Project.objects.filter(status="in_production")
    paginator = Paginator(Project_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sellers = User.objects.all()
    customers = Customer.objects.all()
    current_user = request.user  
    if request.method == 'GET':

        # Renders the customer list view with pagination
        return render(request, 'productionIndex.html', {
            'projects': page_obj,
            'total_projects': Project_list.count(),
            'view': 'production',
            'current_user': current_user, 
            'customers': customers,
            'sellers': sellers   
        })

@login_required
def production_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    return render(request, 'detail_production_project.html', {'project':project})