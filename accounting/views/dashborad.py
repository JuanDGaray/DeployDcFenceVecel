from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounting.models import Account, Transaction
from customer.models import InvoiceProjects
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render

# Dashboard view
@login_required
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
    pending_invoices = InvoiceProjects.objects.filter(status='PENDING').order_by('due_date')[:5]
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

    # Group accounts by account_code
    accounts_grouped_by_code = {}
    for account in accounts:
        if account.account_code not in accounts_grouped_by_code:
            accounts_grouped_by_code[account.account_code] = []
        accounts_grouped_by_code[account.account_code].append(account)

    # Prepare context
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
        'accounts_grouped_by_code': accounts_grouped_by_code,
        'cash_flow_data': cash_flow_data,
    }
    return render(request, 'core/dashboard.html', context)
