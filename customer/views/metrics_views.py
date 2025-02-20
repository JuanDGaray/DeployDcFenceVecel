from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from ..models import Project, ProposalProjects
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncYear 

def project_status_distribution(request):
    status_data = Project.objects.values('status').annotate(count=Count('status'))

    labels = [item['status'] for item in status_data]
    data = [item['count'] for item in status_data]
    return JsonResponse({'labels': labels, 'data': data})


def cost_trend(request):
    cost_data = Project.objects.values('created_at').annotate(
        estimated_cost=Sum('estimated_cost'),
        actual_cost=Sum('actual_cost')
    ).order_by('created_at')

    labels = [item['created_at'].strftime('%Y-%m-%d') for item in cost_data]
    estimated = [item['estimated_cost'] for item in cost_data]
    actual = [item['actual_cost'] for item in cost_data]

    return JsonResponse({
        'labels': labels,
        'estimated': estimated,
        'actual': actual,
    })


def sales_performance_view(request):
    sales_data = (
        Project.objects.values("sales_advisor__username") 
        .annotate(
            total_projects=Count("id"),
            total_estimated_cost=Sum("estimated_cost"), 
            total_actual_cost=Sum("actual_cost"),
        )
        .order_by("-total_projects") 
    )
    return JsonResponse(list(sales_data), safe=False)

def projects_by_creation_date(request):
    group_by = request.GET.get("group_by", "month")  # 'month' o 'year'
    if group_by == "year":
        projects_data = (
            Project.objects.annotate(period=TruncYear("created_at"))
            .values("period")
            .annotate(project_count=Count("id"))
            .order_by("period")
        )
    else:
        projects_data = (
            Project.objects.annotate(period=TruncMonth("created_at"))
            .values("period")
            .annotate(project_count=Count("id"))
            .order_by("period")
        )
    
    chart_data = {
        "labels": [data["period"].strftime("%Y-%m") if group_by == "month" else data["period"].strftime("%Y") for data in projects_data],
        "datasets": [
            {
                "label": "Projects Created",
                "data": [data["project_count"] for data in projects_data],
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "borderColor": "rgba(75, 192, 192, 1)",
                "borderWidth": 1,
                "fill": True,
            }
        ],
    }
    print(chart_data)
    return JsonResponse(chart_data)

def proposals_donut_chart(request):
    approved_proposals = ProposalProjects.objects.filter(status=ProposalProjects.STATUS_APPROVED)
    total_billed = approved_proposals.aggregate(total_billed=Sum('billed_proposal'))['total_billed'] or 0
    total_proposals = approved_proposals.aggregate(total_proposal=Sum('total_proposal'))['total_proposal'] or 0

    data = {
        'total_billed': total_billed,
        'total_proposals': total_proposals,
        'count': approved_proposals.count(),
    }
    print(data)
    return JsonResponse(data)

def metrics(request):
    """
    Vista para renderizar la plantilla del gráfico.
    """
    return render(request, "metrics.html")

