from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Customer, Project, User
from ..form import CustomerForm  # Ensure the correct import for the form
from django.core.paginator import Paginator

# View for listing and adding customers
@login_required
def customers(request):
    """
    Handles the listing of customers and the creation of a new customer. 
    If the request method is GET, it displays a paginated list of customers.
    If the request method is POST, it attempts to create a new customer.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: 
            - Renders the 'customers.html' template with the list of customers and the customer form on GET.
            - Renders the 'customers.html' template with a success or error message after form submission on POST.
    """
    # Retrieves the list of all customers and paginates it
    clients_list = Customer.objects.all()
    paginator = Paginator(clients_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sellers = User.objects.all()
    if request.method == 'GET':
    
        # Renders the customer list view with pagination
        return render(request, 'customers.html', {
            'form': CustomerForm,
            'clients': page_obj,
            'total_clients': clients_list.count(),
            'view': 'costumer',
            'sellers': sellers
        })
    else:
        try:

            form = CustomerForm(request.POST)
            if form.is_valid():
                new_client = form.save(commit=False)
                new_client.sales_advisor = request.user  # Links the customer to the logged-in user
                new_client.save()
                return render(request, 'customers.html', {
                    'form': CustomerForm(),
                    'user_name': request.user,
                    'clients': page_obj,
                    'warning': 'Customer added successfully',
                    'total_clients': clients_list.count(),
                    'view': 'costumer',
                    'sellers': sellers       
                })
            else:
                return render(request, 'customers.html', {
                    'form': CustomerForm(),
                    'user_name': request.user,
                    'clients': page_obj,
                    'warning': 'Invalid data. Please correct the errors.',
                    'total_clients': clients_list.count(),
                    'view': 'costumer',
                    'sellers': sellers       
                })
        except Exception as e:
            # Catch any exception during form handling
            return render(request, 'customers.html', {
                'form': CustomerForm,
                'warning': f'Error: {e}'
            })

# View for displaying details of a single customer
@login_required
def detail_customer(request, client_id):
    """
    Displays the details of a specific customer by their ID.

    Args:
        request (HttpRequest): The HTTP request.
        client_id (int): The ID of the customer to retrieve.

    Returns:
        HttpResponse: Renders the 'details_customer.html' template with the customer's details.
    """
    client = get_object_or_404(Customer, pk=client_id)
    projects = client.projects.all()
    
    # Manejar el caso en el que company_name o first_name pueden estar vacíos o ser None
    if client.customer_type == "company":
        initial = client.company_name[0] if client.company_name else ''
    else:
        initial = client.first_name[0] if client.first_name else ''

    return render(request, 'details_customer.html', {
        'client': client, 
        'initial': initial,
        'projects': projects
    })

# View for editing an existing customer
@login_required
def edit_customer(request, client_id):
    """
    Handles the editing of a customer's details. 
    If the request method is GET, it displays the edit form for the customer.
    If the request method is POST, it saves the changes made to the customer.

    Args:
        request (HttpRequest): The HTTP request.
        client_id (int): The ID of the customer to edit.

    Returns:
        HttpResponse: 
            - Renders the 'edit_customer.html' template with the form pre-filled with customer data on GET.
            - Renders the 'details_customer.html' template showing the updated customer on POST.
    """
    client = get_object_or_404(Customer, pk=client_id)
    if request.method == "GET":
        form = CustomerForm(instance=client)  # Pre-fills the form with the current customer details
        return render(request, 'edit_customer.html', {'client': client, 'form': form})
    else:
        form = CustomerForm(request.POST, instance=client)  # Updates the customer with new data
        if form.is_valid():
            form.save()
            return render(request, 'details_customer.html', {
                'client': client,
                'warning': 'Changes saved successfully',
                'view': 'costumer',
            })
        else:
            return render(request, 'edit_customer.html', {
                'client': client,
                'form': form,
                'warning': 'Invalid data. Please correct the errors.',
                'view': 'costumer',
            })

# View for deleting a customer
@login_required
def delete_customer(request, client_id):
    """
    Handles the deletion of a customer by their ID.

    Args:
        request (HttpRequest): The HTTP request.
        client_id (int): The ID of the customer to delete.

    Returns:
        HttpResponse: Renders the 'customers.html' template with a success message after deletion.
    """
    client = get_object_or_404(Customer, pk=client_id)
    client.delete()  # Deletes the customer
    clients_list = Customer.objects.all()  # Refreshes the customer list after deletion
    paginator = Paginator(clients_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'customers.html', {
        'form': CustomerForm(),
        'clients': page_obj,
        'warning': 'Customer has been deleted successfully',
        'total_clients': clients_list.count(),
        'view': 'costumer',
    })

