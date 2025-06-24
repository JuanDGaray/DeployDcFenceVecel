from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounting.models import Account, Transaction
from customer.models import InvoiceProjects
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render

@login_required
def add_payment_received(request):
    if request.method == 'POST':
        print(request.POST)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
