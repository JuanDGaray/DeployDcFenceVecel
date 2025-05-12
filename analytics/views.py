from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils.timezone import now, datetime
from customer.models import Project, Customer, ProposalProjects
from datetime import timedelta
from customer.views.projects_views import ReviewAnalisisSalesMetrics
from customer.utils import send_email
import json
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse
from collections import defaultdict


base64img = {
    "chart_figure_project": None,
    "chart_figure_client": None,
    "chart_figure_proposal": None,
}
last_obsevations = None

@login_required
def index_analytics(request):
    users = User.objects.all()
    return render(request, 'analytics/index.html', {'users': users})

@login_required
def analytics_dashboard(request, user_id, report_type=None):
    if report_type == 'customer_acquisition':
        return customer_acquisition(user_id)
    else:
        return JsonResponse({'error': 'Invalid report type'}, status=400)
    
@login_required
def daily_analysis(request):
    return performance_daily()

def performance_daily(type=None):
    global base64img
    # Fechas clave para el día anterior
    today = now().date()
    yesterday = today - timedelta(days=1)
    start_datetime = datetime.combine(yesterday, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.min.time())

    # Nombres del día
    actual_day_name = yesterday.strftime('%A %d %B %Y')
    previous_day_name = (yesterday - timedelta(days=1)).strftime('%A %d %B %Y')

    # Proyectos creados el día anterior y el día anterior a ese
    projects_sales_day = Project.objects.filter(
        created_at__gte=start_datetime,
        created_at__lt=end_datetime,
    )
    projects_sales_day_previous = Project.objects.filter(
        created_at__gte=start_datetime - timedelta(days=1),
        created_at__lt=start_datetime,
    )

    proposals_sales_day = ProposalProjects.objects.filter(
        date_created__gte=start_datetime,
        date_created__lt=end_datetime,
    )
    proposals_sales_day_previous = ProposalProjects.objects.filter(
        date_created__gte=start_datetime - timedelta(days=1),
        date_created__lt=start_datetime,
    )

    all_proposals_overdue = ProposalProjects.objects.filter(due_date__lt=now().date()).only('id', 'status', 'due_date', 'sales_advisor_id')
    all_proposals_by_user = defaultdict(list)
    all_proposals = ProposalProjects.objects.only('id', 'status', 'due_date', 'sales_advisor_id')
    all_clients = Customer.objects.only('id', 'customer_type', 'sales_advisor_id')
    all_projects = Project.objects.only('id', 'status', 'sales_advisor_id')

    for proposal in all_proposals_overdue:
        all_proposals_by_user[proposal.sales_advisor_id].append({   
            'id': proposal.id,  
            'status': proposal.status,
            'due_date': proposal.due_date,
            'sales_advisor_id': proposal.sales_advisor_id,
        })

    customer_sales_push = Customer.objects.filter(
        date_created__gte=start_datetime,
        date_created__lt=end_datetime,
    )
    customer_sales_push_previous = Customer.objects.filter(
        date_created__gte=start_datetime - timedelta(days=1),
        date_created__lt=start_datetime,
    )

    status_color_dict = {
        'new': '#0091ff',
        'sent': '#FBBD08',
        'pending': '#F2711C',
        'approved': '#21BA45',
        'rejected': '#ba2121',
        'individual': '#00ccff',
        'company': '#9900fff1',
        'contractor': '#1e8100',
        'quote_sent': '#FBBD08',
        'in_negotiation': '#F2711C',
        'not_approved': '#ba2121',
        'in_production': '#5718cc',
        'pending_payment': '#DB2828',
        'inactive': '#767676',
        'cancelled': '#1B1C1D',
        'contacted': '#ADD8E6',
    }

    customer_by_type = all_clients.values('customer_type').annotate(count=Count('id'))
    total_customers = all_clients.count()
    customer_data = []
    for customer in customer_by_type:
        customer_type = customer['customer_type']
        count = customer['count']
        percentage = (count / total_customers) * 100 if total_customers > 0 else 0
        customer_data.append({
            'customer_type': customer_type,
            'count': count,
            'percentage': round(percentage, 2),
            'color': status_color_dict.get(customer_type, '#000000'),
        })

    proposals_by_status = all_proposals.values('status').annotate(count=Count('id'))
    total_proposals = all_proposals.count()
    proposals_data = []
    for proposal in proposals_by_status:
        status = proposal['status']
        count = proposal['count']
        percentage = (count / total_proposals) * 100 if total_proposals > 0 else 0
        proposals_data.append({
            'status': status,
            'count': count,
            'percentage': round(percentage, 2),
            'color': status_color_dict.get(status, '#000000'),
        })

    projects_by_status = all_projects.values('status').annotate(count=Count('id'))
    total_project = all_projects.count()
    projects_data = []
    for project in projects_by_status:
        status = project['status']
        count = project['count']
        percentage = (count / total_project) * 100 if total_project > 0 else 0
        projects_data.append({
            'status': status,
            'count': count,
            'percentage': round(percentage, 2),
            'color': status_color_dict.get(status, '#000000'),
        })

    issues = []
    for user_id, proposals in all_proposals_by_user.items():
        user = User.objects.filter(id=user_id).first()
        user_name = f"{user.first_name} {user.last_name}" if user else f"User {user_id}"
        issues.append({
            'title': f'Overdue Proposals for {user_name}',
            'message': f'{user_name} has {len(proposals)} overdue proposals that require attention.',
            'description': 'Please review and take action on these proposals. Thank you.',
            'link': 'https://office.dcfence.org/home/proposals_overdue',
            'type': 'danger',
            'proposals': proposals
        })

    if not type == 'email':     
        ia_issues = {
            'issues': issues,
            'users': User.objects.only('id', 'username', 'first_name', 'last_name', 'email').get(id=2),
            'projects_sales_month': projects_sales_day.count(),
            'customer_sales_push': customer_sales_push.count(),
            'proposals_sales_month': proposals_sales_day.count(),
            'actual_month': actual_day_name,
            'previous_month': previous_day_name,
            'projects_sales_month_previous': projects_sales_day_previous.count(),
            'customer_sales_push_previous': customer_sales_push_previous.count(),
            'proposals_sales_month_previous': proposals_sales_day_previous.count(),
            'customer_by_type': customer_by_type,
            'proposals_by_status': proposals_by_status,
            'projects_by_status': projects_by_status,   
            'issues': issues,
        }
        observations = ReviewAnalisisSalesMetrics(ia_issues)
        observations = json.loads(observations)['observations']
        global last_obsevations
        last_obsevations = observations
    else:
        observations = last_obsevations

    context = {
        'user': User.objects.only('id', 'username', 'first_name', 'last_name').get(id=2),
        'projects_sales_month': projects_sales_day,
        'customer_sales_push': customer_sales_push,
        'proposals_sales_month': proposals_sales_day,
        'actual_month': actual_day_name,
        'previous_month': previous_day_name,
        'projects_sales_month_previous': projects_sales_day_previous,
        'customer_sales_push_previous': customer_sales_push_previous,
        'proposals_sales_month_previous': proposals_sales_day_previous,
        'customer_by_type': customer_data,
        'proposals_by_status': proposals_data,
        'projects_by_status': projects_data,
        'issues': issues,
        'observations': observations,
        'base64img': base64img,
        'all_proposals_by_user': dict(all_proposals_by_user),
    }

    html = render_to_string('analytics/components/daily_report.html', context)
    if type == 'email':
        return html

    user = User.objects.get(id=2)
    context = [{
        'user_firth_name': user.first_name,
        'user_last_name': user.last_name,
        'actual_month': actual_day_name,
        'projects_sales_month': projects_sales_day.count(),
        'customer_sales_push': customer_sales_push.count(),
        'proposals_sales_month': proposals_sales_day.count(),
        'customer_by_type': customer_data,
        'proposals_by_status': proposals_data,
        'projects_by_status': projects_data,
    }]
    return JsonResponse(status=200, data={'html': html, 'context': context})




def customer_acquisition(user_id, type=None):
        global base64img
        # Fechas clave
        today = now()
        first_day_current_month = today.replace(day=1)
        first_day_previous_month = (first_day_current_month - timedelta(days=1)).replace(day=1)
        first_day_two_months_ago = (first_day_previous_month - timedelta(days=1)).replace(day=1)

        # Nombres de los meses
        actual_month_name = first_day_previous_month.strftime('%B')  # Mes anterior como actual
        previous_month_name = first_day_two_months_ago.strftime('%B')  # Mes antes del anterior

        # Proyectos creados en el mes anterior (actual en el reporte) y el mes anterior a ese
        projects_sales_month = Project.objects.filter(
            created_at__gte=first_day_previous_month,
            created_at__lt=first_day_current_month,
            sales_advisor_id=user_id
        )
        projects_sales_month_previous = Project.objects.filter(
            created_at__gte=first_day_two_months_ago,
            created_at__lt=first_day_previous_month,
            sales_advisor_id=user_id
        )

        proposals_sales_month = ProposalProjects.objects.filter(
            date_created__gte=first_day_previous_month,
            date_created__lt=first_day_current_month,
            sales_advisor_id=user_id
        )
        
        proposals_sales_month_previous = ProposalProjects.objects.filter(
            date_created__gte=first_day_two_months_ago,
            date_created__lt=first_day_previous_month,
            sales_advisor_id=user_id
        )
        projects_sales_month_previous = Project.objects.filter(
            created_at__gte=first_day_two_months_ago,
            created_at__lt=first_day_previous_month,
            sales_advisor_id=user_id
        )

        # Propuestas creadas en el mes anterior y el mes antes de ese
        # Clientes creados en el mes anterior y el mes antes de ese
        customer_sales_push = Customer.objects.filter(
            date_created__gte=first_day_previous_month,
            date_created__lt=first_day_current_month,
            sales_advisor_id=user_id
        )
        

        customer_sales_push_previous = Customer.objects.filter(
            date_created__gte=first_day_two_months_ago,
            date_created__lt=first_day_previous_month,
            sales_advisor_id=user_id
        )
        
        status_color_dict = {
            'new': '#0091ff',
            'sent': '#FBBD08',
            'pending': '#F2711C',
            'approved': '#21BA45',
            'rejected': '#ba2121',
            'individual': '#00ccff',
            'company': '#9900fff1',
            'contractor': '#1e8100',
            'quote_sent': '#FBBD08',
            'in_negotiation': '#F2711C',
            'not_approved': '#ba2121',
            'in_production': '#5718cc',
            'pending_payment': '#DB2828',
            'inactive': '#767676',
            'cancelled': '#1B1C1D',
            'contacted': '#ADD8E6',
        }

        customer_by_type = customer_sales_push.values('customer_type').annotate(count=Count('id'))
        total_customers = customer_sales_push.count()
        
        customer_data = []
        for customer in customer_by_type:
            customer_type = customer['customer_type']
            count = customer['count']
            percentage = (count / total_customers) * 100 if total_customers > 0 else 0
            customer_data.append({
                'customer_type': customer_type,
                'count': count,
                'percentage': round(percentage, 2),
                'color': status_color_dict.get(customer_type, '#000000'),
            })
            

        # Propuestas por estado
        proposals_by_status = proposals_sales_month.values('status').annotate(count=Count('id'))
        total_proposals = proposals_sales_month.count()
        
        proposals_data = []
        for proposal in proposals_by_status:
            status = proposal['status']
            count = proposal['count']
            percentage = (count / total_proposals) * 100 if total_proposals > 0 else 0
            proposals_data.append({
                'status': status,
                'count': count,
                'percentage': round(percentage, 2),
                'color': status_color_dict.get(status, '#000000'),
            })


        # Proyectos por estado
        projects_by_status = projects_sales_month.values('status').annotate(count=Count('id'))
        total_project = projects_sales_month.count()
        projects_data = []
        for project in projects_by_status:
            status = project['status']
            count = project['count']
            percentage = (count / total_project) * 100 if total_project > 0 else 0
            projects_data.append({
                'status': status,
                'count': count,
                'percentage': round(percentage, 2),
                'color': status_color_dict.get(status, '#000000'),
            })
        
        proposal_overdue = proposals_sales_month.filter(due_date__lt=now().date()).count()
        issues = []
        if proposal_overdue > 0:
            issues.append({
                'title': 'Overdue Proposals',
                'message': f'You have {proposal_overdue} overdue proposals that require your attention.',
                'description': 'Please review and take action on these proposals. Thank you.',
                'link': 'https://office.dcfence.org/home/proposals_overdue',
                'type': 'danger'
            })
        if not type == 'email':
            
            ia_issues = {
                'issues': issues,
                'users': User.objects.only('id', 'username', 'first_name', 'last_name', 'email').get(id=user_id),
                'projects_sales_month': projects_sales_month.count(),
                'customer_sales_push': customer_sales_push.count(),
                'proposals_sales_month': proposals_sales_month.count(),
                'actual_month': actual_month_name,
                'previous_month': previous_month_name,
                'projects_sales_month_previous': projects_sales_month_previous.count(),
                'customer_sales_push_previous': customer_sales_push_previous.count(),
                'proposals_sales_month_previous': proposals_sales_month_previous.count(),
                'customer_by_type': customer_by_type,
                'proposals_by_status': proposals_by_status,
                'projects_by_status': projects_by_status,   
                'issues': issues,
            }
            observations = ReviewAnalisisSalesMetrics(ia_issues)
            observations = json.loads(observations)['observations']
            global last_obsevations
            last_obsevations = observations
        else:
            observations = last_obsevations
            
        
        context = {
            'user': User.objects.only('id', 'username', 'first_name', 'last_name').get(id=user_id),
            'projects_sales_month': projects_sales_month,
            'customer_sales_push': customer_sales_push,
            'proposals_sales_month': proposals_sales_month,
            'actual_month': actual_month_name,
            'previous_month': previous_month_name,
            'projects_sales_month_previous': projects_sales_month_previous,
            'customer_sales_push_previous': customer_sales_push_previous,
            'proposals_sales_month_previous': proposals_sales_month_previous,
            'customer_by_type': customer_data,
            'proposals_by_status': proposals_data,
            'projects_by_status': projects_data,
            'issues': issues,
            'observations': observations,
            'base64img': base64img
        }
        
        html =render_to_string('analytics/components/daily_report.html', context)
        if type == 'email':
            return html
        
        user = User.objects.get(id=user_id)
        context = [{
            'user_firth_name': user.first_name,
            'user_last_name': user.last_name,
            'actual_month': actual_month_name,
            'projects_sales_month': projects_sales_month.count(),
            'customer_sales_push': customer_sales_push.count(),
            'proposals_sales_month': proposals_sales_month.count(),
            'customer_by_type': customer_data,
            'proposals_by_status': proposals_data,
            'projects_by_status': projects_data,
        }]
        return JsonResponse(status=200, data={'html': html, 'context': context})

def send_gmail_metrics(request, user_id):
    global base64img
    html = customer_acquisition(user_id, type='email')
    user = User.objects.get(id=user_id)
    recipient_email = user.email
    subject = 'Monthly Metrics Report by Fenci'
    result = send_email(subject, html, recipient_email)
    return JsonResponse(status=200, data=result)

def send_gmail_daily(request, user_id):
    global base64img
    html = performance_daily(type='email')
    user = User.objects.get(id=user_id)
    recipient_email = user.email
    subject = 'Daily Metrics Report by Fenci'
    result = send_email(subject, html, recipient_email)
    return JsonResponse(status=200, data=result)



def update_base64(request):
    global base64img
    try:
        base64img = json.loads(request.POST.get('base64img'))
        return JsonResponse(status=200, data={'base64img': base64img})
    except Exception as e:
        print(e)
        return JsonResponse(status=500, data={'error': str(e)})
