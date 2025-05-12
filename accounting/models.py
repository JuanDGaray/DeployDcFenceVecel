from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models import Sum

class Account(models.Model):
    ACCOUNT_CATEGORY = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
        ('OTHER', 'Other'),
        ('INTERCOMPANY', 'Intercompany'),
        ('OTHERS_EXPENSES_INCOME', 'Others Expenses Income'),
    ]

    TYPE_ELEMENT = [
        ('ACCOUNT', 'Account'),
        ('SUBACCOUNT', 'Subaccount'),
        ('SUB-SUBACCOUNT', 'Sub-Subaccount'),
        ('GROUP', 'Group'),
        ('SUBGROUP', 'Subgroup'),
        ('ITEMGROUP', 'Itemgroup'),
        ('ITEM', 'Item'),
    ]   

    account_code = models.IntegerField(verbose_name='Account Code', default=0)
    subaccount_code = models.IntegerField(verbose_name='Subaccount Code', null=True, blank=True)
    sub_subaccount_code = models.IntegerField(verbose_name='Sub-Subaccount Code', null=True, blank=True)
    group_code = models.IntegerField(verbose_name='Group Code', null=True, blank=True)
    sub_group_code = models.IntegerField(verbose_name='Sub-Group Code', null=True, blank=True)
    item_group_code = models.IntegerField(verbose_name='Item Group Code', null=True, blank=True)
    item_code = models.IntegerField(verbose_name='Item Code', null=True, blank=True)
    
    name = models.CharField(max_length=100, verbose_name='Name')
    account_type = models.CharField(
        max_length=50, 
        choices=ACCOUNT_CATEGORY, 
        verbose_name='Account Type'
    )
    type_element = models.CharField(
        max_length=20, 
        choices=TYPE_ELEMENT, 
        verbose_name='Type Element',
        default='ACCOUNT'
    )
    description = models.TextField(blank=True, verbose_name='Description')
    initial_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name='Initial Balance'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name='Is Active')
    type_id = models.IntegerField(verbose_name='Type ID', null=True, blank=True)
    parent_account = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='child_accounts',
        on_delete=models.CASCADE
    )
    is_created_by_user = models.BooleanField(default=False, verbose_name='Is Created By User')

    @property
    def balance(self):
        """
        Calculates the current account balance based on the initial balance and transactions.
        """
        credits = self.transactions.filter(transaction_type='CREDIT').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        debits = self.transactions.filter(transaction_type='DEBIT').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if self.account_type in ['ASSET', 'EXPENSE']:
            return self.initial_balance + debits - credits
        else:
            return self.initial_balance + credits - debits

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'




class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('CREDIT', 'Crédito'),
        ('DEBIT', 'Débito'),
    ]

    date = models.DateField(verbose_name='Fecha')
    account = models.ForeignKey(
        Account, 
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='Cuenta'
    )
    transaction_type = models.CharField(
        max_length=10, 
        choices=TRANSACTION_TYPES,
        verbose_name='Tipo de transacción'
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto'
    )
    description = models.TextField(verbose_name='Descripción')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {self.account.name} - {self.get_transaction_type_display()} - {self.amount}"

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-date', '-created_at']
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]

    client = models.CharField(max_length=200, verbose_name='Client')
    date = models.DateField(verbose_name='Date')
    due_date = models.DateField(verbose_name='Due Date')
    total_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Total Amount'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Status'
    )
    description = models.TextField(blank=True, verbose_name='Description')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.id} - {self.client} - {self.total_amount}"

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-date']
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Invoice'
    )
    description = models.CharField(max_length=200, verbose_name='Description')
    quantity = models.PositiveIntegerField(verbose_name='Quantity')
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Unit Price'
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Total'
    )

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"

    class Meta:
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
class Subaccount(models.Model):
    ACCOUNT_TYPES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]

    # Nombre de la subcuenta
    name = models.CharField(max_length=100, verbose_name='Nombre')
    
    # Tipo de cuenta, puede ser el mismo tipo que la cuenta principal
    account_type = models.CharField(
        max_length=20, 
        choices=ACCOUNT_TYPES, 
        verbose_name='Tipo de cuenta'
    )
    
    # Descripción opcional
    description = models.TextField(blank=True, verbose_name='Descripción')

    # Relación con la cuenta principal
    parent_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='subaccounts',  # Este puede quedarse así
        verbose_name='Cuenta principal'
    )
    
    # Saldo inicial de la subcuenta
    initial_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Saldo inicial'
    )

    # Fechas de creación y actualización
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()}) - {self.parent_account.name}"

    @property
    def balance(self):
        """
        Calcula el saldo actual de la subcuenta basándose en el saldo inicial
        y las transacciones asociadas a esta subcuenta.
        """
        # Obtener todas las transacciones de la subcuenta (suponiendo que hay un campo de transacciones en el modelo)
        credits = self.transactions.filter(transaction_type='CREDIT').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        debits = self.transactions.filter(transaction_type='DEBIT').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calcular el saldo
        if self.account_type in ['ASSET', 'EXPENSE']:
            return self.initial_balance + debits - credits
        else:
            return self.initial_balance + credits - debits

    class Meta:
        verbose_name = 'Subcuenta'
        verbose_name_plural = 'Subcuentas'
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('UTILITIES', 'Utilities'),
        ('RENT', 'Rent'),
        ('SALARY', 'Salaries'),
        ('SUPPLIES', 'Supplies'),
        ('OTHER', 'Other'),
    ]

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Category'
    )
    date = models.DateField(verbose_name='Date')
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Amount'
    )
    description = models.TextField(verbose_name='Description')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.date} - {self.amount}"

    class Meta:
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        ordering = ['-date']
class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='User'
    )
    action = models.CharField(
        max_length=10,
        choices=ACTION_TYPES,
        verbose_name='Action'
    )
    model_name = models.CharField(max_length=100, verbose_name='Model')
    object_id = models.PositiveIntegerField(verbose_name='Object ID')
    details = models.TextField(verbose_name='Details')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.model_name}"

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
class Report(models.Model):
    REPORT_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
        ('BALANCE', 'Balance'),
        ('CASH_FLOW', 'Cash Flow'),
    ]

    title = models.CharField(max_length=200, verbose_name='Title')
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        verbose_name='Report Type'
    )
    start_date = models.DateField(verbose_name='Start Date')
    end_date = models.DateField(verbose_name='End Date')
    description = models.TextField(blank=True, verbose_name='Description')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

