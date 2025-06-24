from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from accounting.models import Report, Transaction, Expense  
from accounting.forms import ReportForm
from django.db.models import Sum
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta  



# Report views
class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'core/report_list.html'
    context_object_name = 'reports'

class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'core/report_form.html'
    success_url = reverse_lazy('report-list')

class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'core/report_detail.html'
    context_object_name = 'report'

class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = 'core/report_confirm_delete.html'
    success_url = reverse_lazy('report-list')

@login_required
def financial_report(request):
    # Get date range for the current month
    today = timezone.now().date()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Get financial data
    income = Transaction.objects.filter(
        date__range=[first_day, last_day],
        transaction_type='CREDIT'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    expenses = Transaction.objects.filter(
        date__range=[first_day, last_day],
        transaction_type='DEBIT'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Get transactions by account
    transactions_by_account = Transaction.objects.values(
        'account__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Get expenses by category
    expenses_by_category = Expense.objects.filter(
        date__range=[first_day, last_day]
    ).values(
        'category'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'start_date': first_day,
        'end_date': last_day,
        'income': income,
        'expenses': expenses,
        'balance': income - expenses,
        'transactions_by_account': transactions_by_account,
        'expenses_by_category': expenses_by_category,
    }
    return render(request, 'core/financial_report.html', context)
