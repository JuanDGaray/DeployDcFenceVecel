from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounting.models import Account
from django.shortcuts import render
from decimal import Decimal
from django.contrib import messages

@login_required
def get_accounts_payment(request):
    if request.method == 'GET':
        primary_accounts = Account.objects.filter(parent_account='134')
        grouped_instruments = {}
        
        for primary_account in primary_accounts:
            parent = primary_account.name
            sub_accounts = Account.objects.filter(parent_account=primary_account)
            grouped_instruments[str(parent)] = []
            for sub_account in sub_accounts:
                grouped_instruments[str(parent)].append({
                    'code': sub_account.account_code,
                    'subcode': sub_account.subaccount_code,
                    'subsubcode': sub_account.sub_subaccount_code,
                    'groupcode': sub_account.group_code,
                    'itemgroupcode': sub_account.item_group_code,
                    'name': sub_account.name,
                    'id': sub_account.id
                })
        
        return JsonResponse(status=200, data=grouped_instruments, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


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
