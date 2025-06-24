from django.contrib import admin
from .models import Account, Transaction, InvoiceItem, Expense, AuditLog

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'initial_balance', 'created_at')
    list_filter = ('account_type',)
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'account', 'transaction_type', 'amount', 'created_by')
    list_filter = ('transaction_type', 'date', 'account')
    search_fields = ('description', 'account__name')
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'date', 'amount', 'created_by')
    list_filter = ('category', 'date')
    search_fields = ('description',)
    date_hierarchy = 'date'
    ordering = ('-date',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__username', 'details')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'details', 'created_at')
