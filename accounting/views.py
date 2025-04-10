from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
# from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import Account, Transaction, Invoice, Expense, AuditLog, Report
from .forms import (
    AccountForm, TransactionForm, InvoiceForm, 
    ExpenseForm, InvoiceItemFormSet, UserRegistrationForm,
    ReportForm
)

# Dashboard view
def dashboard(request):
    # Get date range for the current month
    today = timezone.now().date()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get date range for the previous month
    prev_first_day = (first_day - timedelta(days=1)).replace(day=1)
    prev_last_day = first_day - timedelta(days=1)

    # Optimize queries by using annotations and aggregations
    # Get all transactions for the current month in a single query
    current_month_transactions = Transaction.objects.filter(
        date__range=[first_day, last_day]
    ).values('transaction_type').annotate(
        total=Sum('amount')
    )
    
    # Extract values from the annotated queryset
    monthly_income = Decimal('0.00')
    monthly_expenses = Decimal('0.00')
    
    for item in current_month_transactions:
        if item['transaction_type'] == 'CREDIT':
            monthly_income = item['total'] or Decimal('0.00')
        elif item['transaction_type'] == 'DEBIT':
            monthly_expenses = item['total'] or Decimal('0.00')
    
    # Get all transactions for the previous month in a single query
    prev_month_transactions = Transaction.objects.filter(
        date__range=[prev_first_day, prev_last_day]
    ).values('transaction_type').annotate(
        total=Sum('amount')
    )
    
    # Extract values from the annotated queryset
    prev_monthly_income = Decimal('0.00')
    prev_monthly_expenses = Decimal('0.00')
    
    for item in prev_month_transactions:
        if item['transaction_type'] == 'CREDIT':
            prev_monthly_income = item['total'] or Decimal('0.00')
        elif item['transaction_type'] == 'DEBIT':
            prev_monthly_expenses = item['total'] or Decimal('0.00')
    
    # Calculate growth percentages
    income_growth = 0
    if prev_monthly_income > 0:
        income_growth = ((monthly_income - prev_monthly_income) / prev_monthly_income) * 100
    
    expense_growth = 0
    if prev_monthly_expenses > 0:
        expense_growth = ((monthly_expenses - prev_monthly_expenses) / prev_monthly_expenses) * 100
    
    # Calculate total balance using a single query with annotations
    asset_accounts = Account.objects.filter(account_type='ASSET')
    
    # Get initial balance
    initial_balance = asset_accounts.aggregate(
        total=Sum('initial_balance')
    )['total'] or Decimal('0.00')
    
    # Get all asset transactions in a single query
    asset_transactions = Transaction.objects.filter(
        account__account_type='ASSET'
    ).values('transaction_type').annotate(
        total=Sum('amount')
    )
    
    asset_credits = Decimal('0.00')
    asset_debits = Decimal('0.00')
    
    for item in asset_transactions:
        if item['transaction_type'] == 'CREDIT':
            asset_credits = item['total'] or Decimal('0.00')
        elif item['transaction_type'] == 'DEBIT':
            asset_debits = item['total'] or Decimal('0.00')
    
    total_balance = initial_balance + asset_debits - asset_credits
    
    # Calculate previous month balance using a single query
    prev_asset_transactions = Transaction.objects.filter(
        account__account_type='ASSET',
        date__lt=first_day
    ).values('transaction_type').annotate(
        total=Sum('amount')
    )
    
    prev_asset_credits = Decimal('0.00')
    prev_asset_debits = Decimal('0.00')
    
    for item in prev_asset_transactions:
        if item['transaction_type'] == 'CREDIT':
            prev_asset_credits = item['total'] or Decimal('0.00')
        elif item['transaction_type'] == 'DEBIT':
            prev_asset_debits = item['total'] or Decimal('0.00')
    
    prev_total_balance = initial_balance + prev_asset_debits - prev_asset_credits
    
    # Calculate balance change percentage
    balance_change = 0
    if prev_total_balance > 0:
        balance_change = ((total_balance - prev_total_balance) / prev_total_balance) * 100

    # Get recent transactions with select_related to avoid N+1 queries
    recent_transactions = Transaction.objects.select_related('account').order_by('-date')[:5]

    # Get pending invoices - CORREGIDO: Eliminado select_related('client') ya que no es un campo relacional
    pending_invoices = Invoice.objects.filter(status='PENDING').order_by('due_date')[:5]
    pending_invoices_count = pending_invoices.count()
    pending_invoices_amount = sum(invoice.total_amount for invoice in pending_invoices)
    
    # Get all accounts with their balances in a single query
    accounts = Account.objects.all()
    
    # Prepare data for cash flow chart (last 6 months) using a single query
    cash_flow_data = []
    
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get all transactions for this month in a single query
        month_transactions = Transaction.objects.filter(
            date__range=[month_start, month_end]
        ).values('transaction_type').annotate(
            total=Sum('amount')
        )
        
        month_income = Decimal('0.00')
        month_expenses = Decimal('0.00')
        
        for item in month_transactions:
            if item['transaction_type'] == 'CREDIT':
                month_income = item['total'] or Decimal('0.00')
            elif item['transaction_type'] == 'DEBIT':
                month_expenses = item['total'] or Decimal('0.00')
        
        cash_flow_data.append({
            'label': month_date.strftime('%b %Y'),
            'income': float(month_income),
            'expenses': float(month_expenses)
        })

    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'income_growth': income_growth,
        'expense_growth': expense_growth,
        'total_balance': total_balance,
        'balance_change': balance_change,
        'recent_transactions': recent_transactions,
        'pending_invoices': pending_invoices,
        'pending_invoices_count': pending_invoices_count,
        'pending_invoices_amount': pending_invoices_amount,
        'accounts': accounts,
        'cash_flow_data': cash_flow_data,
    }
    return render(request, 'core/dashboard.html', context)

# Account views
class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'core/account_list.html'
    context_object_name = 'accounts'

class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'core/account_form.html'
    success_url = reverse_lazy('account-list')

    def form_valid(self, form):
        # # Get or create a default user for audit logs when user is not authenticated
        # default_user, created = User.objects.get_or_create(
        #     username='system',
        #     defaults={'email': 'system@example.com'}
        # )
        # if created:
        #     default_user.set_password('system123')
        #     default_user.save()

        # form.instance.created_by = self.request.user if self.request.user.is_authenticated else default_user
        response = super().form_valid(form)
        # AuditLog.objects.create(
        #     user=default_user,
        #     action='CREATE',
        #     model_name='Account',
        #     object_id=form.instance.id,
        #     details=f'Created account: {form.instance.name}'
        # )
        return response

class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'core/account_form.html'
    success_url = reverse_lazy('account-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Cuenta'
        return context

    def form_valid(self, form):
        # # Get or create a default user for audit logs when user is not authenticated
        # default_user, created = User.objects.get_or_create(
        #     username='system',
        #     defaults={'email': 'system@example.com'}
        # )
        # if created:
        #     default_user.set_password('system123')
        #     default_user.save()

        response = super().form_valid(form)
        # AuditLog.objects.create(
        #     user=default_user,
        #     action='UPDATE',
        #     model_name='Account',
        #     object_id=form.instance.id,
        #     details=f'Updated account: {form.instance.name}'
        # )
        return response

class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    template_name = 'core/account_confirm_delete.html'
    success_url = reverse_lazy('account-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Cuenta'
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Cuenta eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

# Transaction views
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'core/transaction_list.html'
    context_object_name = 'transactions'

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/transaction_form.html'
    success_url = reverse_lazy('transaction-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set initial date to today
        form.fields['date'].initial = timezone.now().date()
        
        # Add data-account-type attribute to account choices
        form.fields['account'].widget.attrs.update({'class': 'form-select'})
        form.fields['account'].choices = [(account.id, account) for account in Account.objects.all()]
        
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asegurar que las cuentas estén disponibles en el contexto
        context['accounts'] = Account.objects.all()
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/transaction_form.html'
    success_url = reverse_lazy('transaction-list')

class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'core/transaction_confirm_delete.html'
    success_url = reverse_lazy('transaction-list')

# Invoice views
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'core/invoice_list.html'
    context_object_name = 'invoices'

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'core/invoice_form.html'
    success_url = reverse_lazy('invoice-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items'] = InvoiceItemFormSet(self.request.POST)
        else:
            context['items'] = InvoiceItemFormSet()
        return context

    def form_valid(self, form):
        # # Get or create a default user for audit logs when user is not authenticated
        # default_user, created = User.objects.get_or_create(
        #     username='system',
        #     defaults={'email': 'system@example.com'}
        # )
        # if created:
        #     default_user.set_password('system123')
        #     default_user.save()

        context = self.get_context_data()
        items = context['items']
        if items.is_valid():
            # form.instance.created_by = self.request.user if self.request.user.is_authenticated else default_user
            self.object = form.save()
            items.instance = self.object
            items.save()
            # AuditLog.objects.create(
            #     user=default_user,
            #     action='CREATE',
            #     model_name='Invoice',
            #     object_id=form.instance.id,
            #     details=f'Created invoice: {form.instance}'
            # )
            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form))

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'core/invoice_form.html'
    success_url = reverse_lazy('invoice-list')

class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'core/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'core/invoice_detail.html'
    context_object_name = 'invoice'

# Expense views
class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'core/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por fecha
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        category = self.request.GET.get('category')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if category:
            queryset = queryset.filter(category=category)

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['expense_categories'] = Expense.CATEGORY_CHOICES
        return context

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'core/expense_form.html'
    success_url = reverse_lazy('expense-list')

    def get_initial(self):
        return {'date': timezone.now().date()}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'core/expense_form.html'
    success_url = reverse_lazy('expense-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Gasto'
        return context

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'core/expense_confirm_delete.html'
    success_url = reverse_lazy('expense-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Gasto'
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Gasto eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

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
