from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.views.generic.edit import FormMixin
# from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from collections import defaultdict

from .models import Account, Subaccount, Transaction, Invoice, Expense, AuditLog, Report
from .forms import (
    AccountForm, TransactionForm, InvoiceForm, 
    ExpenseForm, InvoiceItemFormSet,
    ReportForm, SubaccountForm
)
from django.http import JsonResponse
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

# Account views
@login_required
def account_list_view(request):
    accounts = get_accounts()
    context = {
        'accounts': accounts,
    }
    return render(request, 'core/account_list.html', context)

def get_accounts():
    accounts_primary = Account.objects.filter(type_element='ACCOUNT').select_related('parent_account').order_by('account_code')
    subaccounts = Account.objects.filter(type_element='SUBACCOUNT').select_related('parent_account').order_by('account_code','subaccount_code')
    sub_sub_accounts = Account.objects.filter(type_element='SUB-SUBACCOUNT').select_related('parent_account').order_by('account_code','subaccount_code','sub_subaccount_code')
    group_accounts = Account.objects.filter(type_element='GROUP').select_related('parent_account').order_by('account_code','subaccount_code', 'group_code')
    sub_group_accounts = Account.objects.filter(type_element='SUBGROUP').select_related('parent_account').order_by('account_code','subaccount_code','group_code', 'sub_group_code')
    item_group_accounts = Account.objects.filter(type_element='ITEMGROUP').select_related('parent_account').order_by('account_code','subaccount_code','group_code', 'sub_group_code', 'item_group_code')
    item_accounts = Account.objects.filter(type_element='ITEMs').select_related('parent_account').order_by('account_code','subaccount_code','group_code', 'sub_group_code', 'item_group_code', 'item_code')

    # Agrupa cuentas principales por tipo
    accounts = {
        'Assets': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
        'Liabilities': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
        'Equity': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
        'Revenue': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
        'Expenses': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
        'Others Expenses Income': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
        'Other': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
        'Intercompany': {
            'accounts': [],
            'subaccounts': {},
            'sub_subaccounts': {},
            'groups': {},
            'subgroups': {},
            'itemgroups': {},
            'items': {},
        },
    }
    for account in accounts_primary:
        if account.account_type == 'ASSETS':
            accounts['Assets']['accounts'].append(account)
        elif account.account_type == 'LIABILITIES':
            accounts['Liabilities']['accounts'].append(account)
        elif account.account_type == 'EQUITY':
            accounts['Equity']['accounts'].append(account)      
        elif account.account_type == 'REVENUE':
            accounts['Revenue']['accounts'].append(account)
        elif account.account_type == 'EXPENSES':
            accounts['Expenses']['accounts'].append(account)
        elif account.account_type == 'OTHERS_EXPENSES_INCOME':
            accounts['Others Expenses Income']['accounts'].append(account)
        elif account.account_type == 'OTHER':
            accounts['Other']['accounts'].append(account)
        elif account.account_type == 'INTERCOMPANY':
            accounts['Intercompany']['accounts'].append(account)

    for sub in subaccounts:
        if sub.parent_account:
            if sub.parent_account.account_type == 'ASSETS':
                if sub.parent_account.name not in accounts['Assets']['subaccounts']:
                    accounts['Assets']['subaccounts'][sub.parent_account.name] = []
                accounts['Assets']['subaccounts'][sub.parent_account.name].append(sub)
            elif sub.parent_account.account_type == 'LIABILITIES':
                if sub.parent_account.name not in accounts['Liabilities']['subaccounts']:
                    accounts['Liabilities']['subaccounts'][sub.parent_account.name] = []
                accounts['Liabilities']['subaccounts'][sub.parent_account.name].append(sub)
            elif sub.parent_account.account_type == 'EQUITY':
                if sub.parent_account.name not in accounts['Equity']['subaccounts']:
                    accounts['Equity']['subaccounts'][sub.parent_account.name] = []
                accounts['Equity']['subaccounts'][sub.parent_account.name].append(sub)
            elif sub.parent_account.account_type == 'REVENUE':
                if sub.parent_account.name not in accounts['Revenue']['subaccounts']:
                    accounts['Revenue']['subaccounts'][sub.parent_account.name] = []
                accounts['Revenue']['subaccounts'][sub.parent_account.name].append(sub)
            elif sub.parent_account.account_type == 'EXPENSES':
                if sub.parent_account.name not in accounts['Expenses']['subaccounts']:
                    accounts['Expenses']['subaccounts'][sub.parent_account.name] = []
                accounts['Expenses']['subaccounts'][sub.parent_account.name].append(sub)
            elif sub.parent_account.account_type == 'OTHERS_EXPENSES_INCOME':
                if sub.parent_account.name not in accounts['Others Expenses Income']['subaccounts']:
                    accounts['Others Expenses Income']['subaccounts'][sub.parent_account.name] = []
                accounts['Others Expenses Income']['subaccounts'][sub.parent_account.name].append(sub)
            elif sub.parent_account.account_type == 'OTHER':
                if sub.parent_account.name not in accounts['Other']['subaccounts']:
                    accounts['Other']['subaccounts'][sub.parent_account.name] = []
                accounts['Other']['subaccounts'][sub.parent_account.name].append(sub)
            elif sub.parent_account.account_type == 'INTERCOMPANY':
                if sub.parent_account.name not in accounts['Intercompany']['subaccounts']:
                    accounts['Intercompany']['subaccounts'][sub.parent_account.name] = []
                accounts['Intercompany']['subaccounts'][sub.parent_account.name].append(sub)        

    for sub_sub in sub_sub_accounts:
        if sub_sub.parent_account:
            if sub_sub.parent_account.account_type == 'ASSETS':
                if sub_sub.parent_account.name not in accounts['Assets']['sub_subaccounts']:
                    accounts['Assets']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Assets']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)
            elif sub_sub.parent_account.account_type == 'LIABILITIES':
                if sub_sub.parent_account.name not in accounts['Liabilities']['sub_subaccounts']:
                    accounts['Liabilities']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Liabilities']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)
            elif sub_sub.parent_account.account_type == 'EQUITY':
                if sub_sub.parent_account.name not in accounts['Equity']['sub_subaccounts']:
                    accounts['Equity']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Equity']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)
            elif sub_sub.parent_account.account_type == 'REVENUE':      
                if sub_sub.parent_account.name not in accounts['Revenue']['sub_subaccounts']:
                    accounts['Revenue']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Revenue']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)
            elif sub_sub.parent_account.account_type == 'EXPENSES':
                if sub_sub.parent_account.name not in accounts['Expenses']['sub_subaccounts']:
                    accounts['Expenses']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Expenses']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)
            elif sub_sub.parent_account.account_type == 'OTHERS_EXPENSES_INCOME':
                if sub_sub.parent_account.name not in accounts['Others Expenses Income']['sub_subaccounts']:
                    accounts['Others Expenses Income']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Others Expenses Income']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)
            elif sub_sub.parent_account.account_type == 'OTHER':
                if sub_sub.parent_account.name not in accounts['Other']['sub_subaccounts']:
                    accounts['Other']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Other']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)
            elif sub_sub.parent_account.account_type == 'INTERCOMPANY':
                if sub_sub.parent_account.name not in accounts['Intercompany']['sub_subaccounts']:
                    accounts['Intercompany']['sub_subaccounts'][sub_sub.parent_account.name] = []
                accounts['Intercompany']['sub_subaccounts'][sub_sub.parent_account.name].append(sub_sub)    
                
    for group in group_accounts:
        if group.parent_account:
            if group.parent_account.account_type == 'ASSETS':
                if group.parent_account.name not in accounts['Assets']['groups']:
                    accounts['Assets']['groups'][group.parent_account.name] = []
                accounts['Assets']['groups'][group.parent_account.name].append(group)
            elif group.parent_account.account_type == 'LIABILITIES':
                if group.parent_account.name not in accounts['Liabilities']['groups']:
                    accounts['Liabilities']['groups'][group.parent_account.name] = []
                accounts['Liabilities']['groups'][group.parent_account.name].append(group)
            elif group.parent_account.account_type == 'EQUITY':
                if group.parent_account.name not in accounts['Equity']['groups']:
                    accounts['Equity']['groups'][group.parent_account.name] = []
                accounts['Equity']['groups'][group.parent_account.name].append(group)
            elif group.parent_account.account_type == 'REVENUE':
                if group.parent_account.name not in accounts['Revenue']['groups']:
                    accounts['Revenue']['groups'][group.parent_account.name] = []
                accounts['Revenue']['groups'][group.parent_account.name].append(group)
            elif group.parent_account.account_type == 'EXPENSES':
                if group.parent_account.name not in accounts['Expenses']['groups']:
                    accounts['Expenses']['groups'][group.parent_account.name] = []
                accounts['Expenses']['groups'][group.parent_account.name].append(group)
            elif group.parent_account.account_type == 'OTHERS_EXPENSES_INCOME':
                if group.parent_account.name not in accounts['Others Expenses Income']['groups']:
                    accounts['Others Expenses Income']['groups'][group.parent_account.name] = []
                accounts['Others Expenses Income']['groups'][group.parent_account.name].append(group)
            elif group.parent_account.account_type == 'OTHER':
                if group.parent_account.name not in accounts['Other']['groups']:
                    accounts['Other']['groups'][group.parent_account.name] = []
                accounts['Other']['groups'][group.parent_account.name].append(group)
            elif group.parent_account.account_type == 'INTERCOMPANY':
                if group.parent_account.name not in accounts['Intercompany']['groups']:
                    accounts['Intercompany']['groups'][group.parent_account.name] = []
                accounts['Intercompany']['groups'][group.parent_account.name].append(group)

    for sub_group in sub_group_accounts:
        if sub_group.parent_account:
            if sub_group.parent_account.account_type == 'ASSETS':
                if sub_group.parent_account.name not in accounts['Assets']['subgroups']:
                    accounts['Assets']['subgroups'][sub_group.parent_account.name] = []
                accounts['Assets']['subgroups'][sub_group.parent_account.name].append(sub_group) 
            elif sub_group.parent_account.account_type == 'LIABILITIES':
                if sub_group.parent_account.name not in accounts['Liabilities']['subgroups']:
                    accounts['Liabilities']['subgroups'][sub_group.parent_account.name] = []
                accounts['Liabilities']['subgroups'][sub_group.parent_account.name].append(sub_group)
            elif sub_group.parent_account.account_type == 'EQUITY':
                if sub_group.parent_account.name not in accounts['Equity']['subgroups']:
                    accounts['Equity']['subgroups'][sub_group.parent_account.name] = []
                accounts['Equity']['subgroups'][sub_group.parent_account.name].append(sub_group)
            elif sub_group.parent_account.account_type == 'REVENUE':
                if sub_group.parent_account.name not in accounts['Revenue']['subgroups']:
                    accounts['Revenue']['subgroups'][sub_group.parent_account.name] = []
                accounts['Revenue']['subgroups'][sub_group.parent_account.name].append(sub_group)
            elif sub_group.parent_account.account_type == 'EXPENSES':
                if sub_group.parent_account.name not in accounts['Expenses']['subgroups']:
                    accounts['Expenses']['subgroups'][sub_group.parent_account.name] = []
                accounts['Expenses']['subgroups'][sub_group.parent_account.name].append(sub_group)
            elif sub_group.parent_account.account_type == 'OTHERS_EXPENSES_INCOME':
                if sub_group.parent_account.name not in accounts['Others Expenses Income']['subgroups']:
                    accounts['Others Expenses Income']['subgroups'][sub_group.parent_account.name] = []
                accounts['Others Expenses Income']['subgroups'][sub_group.parent_account.name].append(sub_group)
            elif sub_group.parent_account.account_type == 'OTHER':
                if sub_group.parent_account.name not in accounts['Other']['subgroups']:
                    accounts['Other']['subgroups'][sub_group.parent_account.name] = []
                accounts['Other']['subgroups'][sub_group.parent_account.name].append(sub_group)
            elif sub_group.parent_account.account_type == 'INTERCOMPANY':
                if sub_group.parent_account.name not in accounts['Intercompany']['subgroups']:
                    accounts['Intercompany']['subgroups'][sub_group.parent_account.name] = []
                accounts['Intercompany']['subgroups'][sub_group.parent_account.name].append(sub_group)   
                
    for item_group in item_group_accounts:
        if item_group.parent_account:
            if item_group.parent_account.account_type == 'ASSETS':
                if item_group.parent_account.name not in accounts['Assets']['itemgroups']:
                    accounts['Assets']['itemgroups'][item_group.parent_account.name] = []
                accounts['Assets']['itemgroups'][item_group.parent_account.name].append(item_group)
            elif item_group.parent_account.account_type == 'LIABILITIES':
                if item_group.parent_account.name not in accounts['Liabilities']['itemgroups']:
                    accounts['Liabilities']['itemgroups'][item_group.parent_account.name] = []
                accounts['Liabilities']['itemgroups'][item_group.parent_account.name].append(item_group)
            elif item_group.parent_account.account_type == 'EQUITY':
                if item_group.parent_account.name not in accounts['Equity']['itemgroups']:
                    accounts['Equity']['itemgroups'][item_group.parent_account.name] = []
                accounts['Equity']['itemgroups'][item_group.parent_account.name].append(item_group)
            elif item_group.parent_account.account_type == 'REVENUE':
                if item_group.parent_account.name not in accounts['Revenue']['itemgroups']:
                    accounts['Revenue']['itemgroups'][item_group.parent_account.name] = []
                accounts['Revenue']['itemgroups'][item_group.parent_account.name].append(item_group)
            elif item_group.parent_account.account_type == 'EXPENSES':
                if item_group.parent_account.name not in accounts['Expenses']['itemgroups']:
                    accounts['Expenses']['itemgroups'][item_group.parent_account.name] = []
                accounts['Expenses']['itemgroups'][item_group.parent_account.name].append(item_group)
            elif item_group.parent_account.account_type == 'OTHERS_EXPENSES_INCOME':
                if item_group.parent_account.name not in accounts['Others Expenses Income']['itemgroups']:
                    accounts['Others Expenses Income']['itemgroups'][item_group.parent_account.name] = []
                accounts['Others Expenses Income']['itemgroups'][item_group.parent_account.name].append(item_group)
            elif item_group.parent_account.account_type == 'OTHER':
                if item_group.parent_account.name not in accounts['Other']['itemgroups']:
                    accounts['Other']['itemgroups'][item_group.parent_account.name] = []
                accounts['Other']['itemgroups'][item_group.parent_account.name].append(item_group)
            elif item_group.parent_account.account_type == 'INTERCOMPANY':
                if item_group.parent_account.name not in accounts['Intercompany']['itemgroups']:
                    accounts['Intercompany']['itemgroups'][item_group.parent_account.name] = []
                accounts['Intercompany']['itemgroups'][item_group.parent_account.name].append(item_group)
                
    for item in item_accounts:
        if item.parent_account:
            if item.parent_account.account_type == 'ASSETS':
                if item.parent_account.name not in accounts['Assets']['items']:
                    accounts['Assets']['items'][item.parent_account.name] = []
                accounts['Assets']['items'][item.parent_account.name].append(item)
            elif item.parent_account.account_type == 'LIABILITIES':
                if item.parent_account.name not in accounts['Liabilities']['items']:
                    accounts['Liabilities']['items'][item.parent_account.name] = []
                accounts['Liabilities']['items'][item.parent_account.name].append(item)
            elif item.parent_account.account_type == 'EQUITY':
                if item.parent_account.name not in accounts['Equity']['items']:
                    accounts['Equity']['items'][item.parent_account.name] = []
                accounts['Equity']['items'][item.parent_account.name].append(item)
            elif item.parent_account.account_type == 'REVENUE':
                if item.parent_account.name not in accounts['Revenue']['items']:
                    accounts['Revenue']['items'][item.parent_account.name] = []
                accounts['Revenue']['items'][item.parent_account.name].append(item)  
            elif item.parent_account.account_type == 'EXPENSES':
                if item.parent_account.name not in accounts['Expenses']['items']:
                    accounts['Expenses']['items'][item.parent_account.name] = []
                accounts['Expenses']['items'][item.parent_account.name].append(item)
            elif item.parent_account.account_type == 'OTHERS_EXPENSES_INCOME':
                if item.parent_account.name not in accounts['Others Expenses Income']['items']:
                    accounts['Others Expenses Income']['items'][item.parent_account.name] = []
                accounts['Others Expenses Income']['items'][item.parent_account.name].append(item)
            elif item.parent_account.account_type == 'OTHER':
                if item.parent_account.name not in accounts['Other']['items']:
                    accounts['Other']['items'][item.parent_account.name] = []
                accounts['Other']['items'][item.parent_account.name].append(item)
            elif item.parent_account.account_type == 'INTERCOMPANY':
                if item.parent_account.name not in accounts['Intercompany']['items']:    
                    accounts['Intercompany']['items'][item.parent_account.name] = []
                accounts['Intercompany']['items'][item.parent_account.name].append(item)
    return accounts

@login_required
def add_account(request):
    if request.method == 'POST':
        print(request.POST)
        account = Account(
            account_code=int(request.POST.get('account_code', 0)) if request.POST.get('account_code') != 'None' else 0,
            subaccount_code=int(request.POST.get('subaccount_code')) if request.POST.get('subaccount_code') and request.POST.get('subaccount_code') != 'None' else None,
            sub_subaccount_code=int(request.POST.get('subsubaccount_code')) if request.POST.get('subsubaccount_code') and request.POST.get('subsubaccount_code') != 'None' else None,
            group_code=int(request.POST.get('group_code')) if request.POST.get('group_code') and request.POST.get('group_code') != 'None' else None,
            item_group_code=int(request.POST.get('new_item_group')) if request.POST.get('new_item_group') and request.POST.get('new_item_group') != 'None' else None,
            type_id=int(request.POST.get('account_type_id')) if request.POST.get('account_type_id') and request.POST.get('account_type_id') != 'None' else None,
            type_element=request.POST.get('type_element'),
            name=request.POST.get('account_name', ''),
            description=request.POST.get('account_description', ''),
            initial_balance=Decimal(request.POST.get('initial_balance', 0)),
            is_active=bool(request.POST.get('is_active', False)),
            parent_account_id=int(request.POST.get('account_parent')) if request.POST.get('account_parent') and request.POST.get('account_parent') != 'None' else None,
            is_created_by_user=True,
            account_type=request.POST.get('account_type')
            
        )
        
        print(account)  # Debug print
        account.save()
        messages.success(request, 'Account created successfully!')
        return JsonResponse({'success': True})

@login_required
def delete_account(request):
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        print(account_id)
        account = Account.objects.get(pk=account_id)
        account.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

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
