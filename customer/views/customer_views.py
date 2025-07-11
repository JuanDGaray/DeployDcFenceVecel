from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from ..models import Customer, Project
from django.contrib.auth.models import User
from ..form import CustomerForm 
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from ..models import ProposalProjects, InvoiceProjects, ProjectHistory, Project
from collections import Counter
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import json
from ..utils import get_email_full_content
import base64

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
    

    if request.method == 'GET':
        # Renders the customer list view with pagination
        sellers = User.objects.only('id', 'first_name', 'last_name', 'username').order_by('first_name')
        return render(request, 'customers.html', {
            'form': CustomerForm(),
            'view': 'costumer',
            'sellers': sellers
        })
    else:  # If the request method is POST
        try:
            sellers = User.objects.only('id', 'first_name', 'last_name', 'username').order_by('first_name')
            form = CustomerForm(request.POST)
            if form.is_valid():
                new_client = form.save(commit=False)
                new_client.sales_advisor = request.user  # Links the customer to the logged-in user
                new_client.save()

                # Redirect to the same page with a GET request to avoid form resubmission on page reload
                return redirect('customers')  # Replace 'customers' with the correct URL name for this view

            else:
                # If the form is invalid, reload the page with the error messages
                return render(request, 'customers.html', {
                    'form': form,
                    'warning': 'Invalid data. Please correct the errors.',
                    'view': 'costumer',
                    'sellers': sellers
                })
        except Exception as e:
            # Catch any exception during form handling
            return render(request, 'customers.html', {
                'form': CustomerForm(),
                'warning': f'Error: {e}',
                'view': 'costumer',
                'sellers': sellers
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
    projects = client.projects.all().order_by('-created_at')
    
    # Calcular métricas financieras
    total_billed = InvoiceProjects.objects.filter(
        project__customer=client
    ).aggregate(total=Sum('total_invoice'))['total'] or 0
    
    total_paid = InvoiceProjects.objects.filter(
        project__customer=client
    ).aggregate(total=Sum('total_paid'))['total'] or 0
    
    total_pending = total_billed - total_paid
    
    # Calcular porcentaje de pago
    payment_percentage = 0
    if total_billed > 0:
        payment_percentage = (total_paid / total_billed) * 100
    
    # Contar propuestas
    total_proposals = ProposalProjects.objects.filter(
        project__customer=client
    ).count()
    
    # Obtener propuestas recientes
    proposals = ProposalProjects.objects.filter(
        project__customer=client
    ).select_related('project').order_by('-date_created')[:5]
    
    # Obtener facturas recientes
    invoices = InvoiceProjects.objects.filter(
        project__customer=client
    ).select_related('project').order_by('-date_created')[:5]
    
    # Obtener actividad reciente
    recent_activity = ProjectHistory.objects.filter(
        project__customer=client
    ).select_related('user', 'project').order_by('-timestamp')[:10]

    # Calcular distribución de estados de proyectos
    project_status_distribution = {}
    if projects.exists():
        for project in projects:
            status = project.status
            project_status_distribution[status] = project_status_distribution.get(status, 0) + 1
    
    # Manejar el caso en el que company_name o first_name pueden estar vacíos o ser None
    if client.customer_type == "company":
        initial = client.company_name[0] if client.company_name else ''
    else:
        initial = client.first_name[0] if client.first_name else ''

    return render(request, 'details_customer.html', {
        'client': client, 
        'initial': initial,
        'projects': projects,
        'total_billed': total_billed,
        'total_pending': total_pending,
        'total_proposals': total_proposals,
        'proposals': proposals,
        'invoices': invoices,
        'recent_activity': recent_activity,
        'project_status_distribution': project_status_distribution,
        'total_paid': total_paid,
        'payment_percentage': payment_percentage
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

@csrf_exempt
def get_client_emails(request):
    """
    Vista para obtener todos los correos enviados a un cliente específico.
    
    Método: GET
    Parámetros:
    - client_email: Correo del cliente a buscar
    - project_id (opcional): ID del proyecto para filtrar por P{project_id} en el asunto
    - start_date (opcional): Fecha de inicio en formato YYYY/MM/DD
    - end_date (opcional): Fecha de fin en formato YYYY/MM/DD
    """
    if request.method == 'GET':
        try:
            client_email = request.GET.get('client_email')
            project_id = request.GET.get('project_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if not client_email:
                return JsonResponse({
                    'status': 'error',
                    'message': 'El parámetro client_email es requerido'
                }, status=400)
            
            # Si se proporcionan fechas, usar la función con filtro de fechas
            if start_date or end_date:
                from ..utils import get_emails_by_date_range
                result = get_emails_by_date_range(client_email, start_date, end_date)
            else:
                # Usar la función básica sin filtro de fechas
                from ..utils import get_emails_sent_to_client
                # Si se proporciona project_id, filtrar por ese proyecto
                if project_id:
                    result = get_emails_sent_to_client(client_email, int(project_id))
                else:
                    result = get_emails_sent_to_client(client_email)
            
            if result['status'] == 'success':
                return JsonResponse(result, status=200)
            else:
                return JsonResponse(result, status=500)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error inesperado: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


@csrf_exempt
def emails_sent_to_client_view(request, project_id):
    """
    Vista para mostrar emails enviados a un cliente específico con información de tracking.
    """
    if request.method == 'GET':
        try:
            # Obtener el email del cliente desde el proyecto
            project = get_object_or_404(Project, pk=project_id)
            client_email = project.customer.email
            
            # Obtener emails enviados
            from ..utils import get_emails_sent_to_client, get_project_email_tracking
            result = get_emails_sent_to_client(client_email, project_id)
            
            # Obtener información de tracking
            tracking_info = get_project_email_tracking(project_id)
            
            # Combinar información de emails con tracking
            emails_with_tracking = []
            for email in result.get('emails', []):
                # Buscar tracking por subject (que contiene el tracking_id)
                email_tracking = None
                for tracking in tracking_info:
                    if tracking['tracking_id'] in email.get('subject', ''):
                        email_tracking = tracking
                        break
                
                email_info = {
                    **email,
                    'tracking': email_tracking,
                    'is_opened': email_tracking['is_opened'] if email_tracking else False,
                    'opened_count': email_tracking['opened_count'] if email_tracking else 0,
                    'opened_at': email_tracking['opened_at'] if email_tracking else None
                }
                emails_with_tracking.append(email_info)
            
            return JsonResponse({
                'status': 'success',
                'emails': emails_with_tracking,
                'tracking_summary': {
                    'total_emails': len(emails_with_tracking),
                    'opened_emails': len([e for e in emails_with_tracking if e['is_opened']]),
                    'total_opens': sum([e['opened_count'] for e in emails_with_tracking])
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@csrf_exempt
def send_proposal_email(request, project_id, proposal_id):
    """
    Vista para enviar propuesta por correo electrónico con PDF adjunto.
    
    Método: POST
    Parámetros:
    - recipient_email: Email del destinatario
    - recipient_name: Nombre del destinatario
    - subject: Asunto del correo
    - body: Cuerpo del mensaje (HTML)
    - project_id: ID del proyecto
    - proposal_id: ID de la propuesta
    - additional_recipients: Lista JSON de destinatarios adicionales
    - send_copy_to_sales: Boolean para enviar copia al sales advisor
    """
    if request.method == 'POST':
        try:
            import json
            
            # Obtener datos del formulario
            recipient_email = request.POST.get('recipient_email')
            recipient_name = request.POST.get('recipient_name', '')
            original_subject = request.POST.get('subject')
            body = request.POST.get('body')
            additional_recipients_json = request.POST.get('additional_recipients', '[]')
            send_copy_to_sales = request.POST.get('send_copy_to_sales', 'false').lower() == 'true'
            
            
            # Agregar identificador único al asunto
            unique_id = f"P{project_id} Pr{proposal_id}"
            subject = f"{original_subject} | {unique_id}"
            


            # Validar campos requeridos
            if not all([recipient_email, subject, body]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All required fields must be provided'
                }, status=400)
            
            # Obtener proyecto y propuesta
            project = get_object_or_404(Project, pk=project_id)
            proposal = get_object_or_404(ProposalProjects, pk=proposal_id, project=project)
            
            # Renderizar el template de email con la información de la propuesta
            from django.template.loader import render_to_string
            
            # Renderizar el template de email
            email_html_content = render_to_string('components/email_proposal_email.html', {
                'proposal': proposal,
                'project': project,
            })
            
            # Enviar email con el template renderizado
            from ..utils import send_email
            
            # Combinar el mensaje personalizado con el HTML del template
            combined_html = f"""
            <div style="line-height: 0; font-family: Arial, sans-serif; margin-bottom: 20px;">
                {body}
            </div>
            
            <hr style="margin: 30px 0; border: 1px solid #ddd;">
            
            <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin-top: 20px;">
                {email_html_content}
            </div>
            """
            
            # Lista de todos los destinatarios
            all_recipients = [recipient_email]
            
            # Agregar destinatarios adicionales
            try:
                additional_recipients = json.loads(additional_recipients_json)
                for recipient in additional_recipients:
                    if recipient.get('email'):
                        all_recipients.append(recipient['email'])
            except json.JSONDecodeError:
                pass
            
            # Agregar sales advisor si está marcado
            if send_copy_to_sales and request.user.email:
                all_recipients.append(request.user.email)
            
            # Enviar email a todos los destinatarios
            success_count = 0
            error_messages = []
            
            
            for email in all_recipients:
                result = send_email(
                    subject=subject,
                    html_body=combined_html,
                    recipient_email=email,
                    project_id=project_id,
                    proposal_id=proposal_id
                )
                
                if result['status'] == 'success':
                    success_count += 1
                else:
                    error_msg = f"Error sending to {email}: {result['message']}"
                    error_messages.append(error_msg)

            
            
            if success_count > 0:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Email sent successfully to {success_count} recipient(s)',
                    'details': error_messages if error_messages else None
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to send email to any recipient',
                    'details': error_messages
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@csrf_exempt
def get_emails_by_project_proposal_view(request):
    """
    Vista para obtener todos los correos relacionados con un proyecto y propuesta específicos.
    
    Método: GET
    Parámetros:
    - project_id: ID del proyecto
    - proposal_id: ID de la propuesta
    """
    if request.method == 'GET':
        try:
            project_id = request.GET.get('project_id')
            proposal_id = request.GET.get('proposal_id')
            
            if not project_id or not proposal_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'project_id y proposal_id son requeridos'
                }, status=400)
            
            from ..utils import get_emails_by_project_proposal
            result = get_emails_by_project_proposal(int(project_id), int(proposal_id))
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error inesperado: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@csrf_exempt
def reply_email(request):
    """
    Endpoint para enviar una respuesta a un email recibido.
    Método: POST
    Parámetros:
    - recipient_email: Email del destinatario
    - subject: Asunto del correo
    - body: Cuerpo del mensaje (HTML)
    - original_message_id: ID del mensaje original (opcional)
    """
    if request.method == 'POST':
        try:
            recipient_email = request.POST.get('recipient_email')
            subject = request.POST.get('subject')
            body = request.POST.get('body')
            original_message_id = request.POST.get('original_message_id')
            
            if not all([recipient_email, subject, body]):
                return JsonResponse({'status': 'error', 'message': 'All required fields must be provided'}, status=400)
            
            from ..utils import send_reply_email
            
            # Enviar email como respuesta
            result = send_reply_email(
                subject=subject, 
                html_body=body, 
                recipient_email=recipient_email,
                original_message_id=original_message_id
            )
            
            if result['status'] == 'success':
                return JsonResponse({'status': 'success', 'message': 'Reply sent successfully!'})
            else:
                return JsonResponse({'status': 'error', 'message': result.get('message', 'Unknown error')}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def mark_email_as_read(request):
    """
    Marca un email como leído usando Gmail API.
    Método: POST
    Parámetros:
    - email_id: ID del email a marcar como leído
    """
    if request.method == 'POST':
        try:
            email_id = request.POST.get('email_id')
            if not email_id:
                return JsonResponse({'status': 'error', 'message': 'Email ID is required'}, status=400)
            
            # Usar Gmail API para remover la label 'UNREAD'
            from ..utils import GoogleService
            service = GoogleService.get_service()['gmail']
            
            # Modificar las labels del mensaje para remover 'UNREAD'
            service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Email marked as read'
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def download_email_attachment(request):
    """
    Vista para descargar archivos adjuntos de emails (sirve para descarga y previsualización).
    """
    if request.method == 'POST':
        try:
            print("download_email_attachment")
            data = json.loads(request.body)
            message_id = data.get('message_id')
            attachment_id = data.get('attachment_id')
            filename = data.get('filename', 'attachment')
            mime_type = data.get('mime_type', 'application/octet-stream')
            print(message_id, attachment_id, filename)
            if not all([message_id, attachment_id]):
                print("error")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Message ID and attachment ID are required'
                }, status=400)

            try:
                from ..utils import GoogleService
                service = GoogleService.get_service()['gmail']
                gmail_attachment = service.users().messages().attachments().get(
                    userId='me',
                    messageId=message_id,
                    id=attachment_id
                ).execute()
                attachment_data = gmail_attachment['data']
                decoded_data = base64.urlsafe_b64decode(attachment_data + '=' * (-len(attachment_data) % 4))
                
                response = HttpResponse(decoded_data, content_type=mime_type)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except Exception as e:
                print("error 2")
                print(e)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error getting attachment'
                }, status=500)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }, status=500)
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST method is allowed'
    }, status=405)



