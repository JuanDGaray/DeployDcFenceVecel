from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models import Sum

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('ASSET', 'Activo'),
        ('LIABILITY', 'Pasivo'),
        ('EQUITY', 'Capital'),
        ('INCOME', 'Ingreso'),
        ('EXPENSE', 'Gasto'),
    ]

    name = models.CharField(max_length=100, verbose_name='Nombre')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, verbose_name='Tipo de cuenta')
    description = models.TextField(blank=True, verbose_name='Descripción')
    initial_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Saldo inicial'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

    @property
    def balance(self):
        """
        Calcula el balance actual de la cuenta basado en el saldo inicial y las transacciones.
        """
        # Obtener todas las transacciones de la cuenta
        credits = self.transactions.filter(transaction_type='CREDIT').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        debits = self.transactions.filter(transaction_type='DEBIT').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calcular el balance según el tipo de cuenta
        if self.account_type in ['ASSET', 'EXPENSE']:
            # Para activos y gastos, los débitos aumentan y los créditos disminuyen
            return self.initial_balance + debits - credits
        else:
            # Para pasivos, ingresos y capital, los créditos aumentan y los débitos disminuyen
            return self.initial_balance + credits - debits

    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'

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
        ('PENDING', 'Pendiente'),
        ('PAID', 'Pagado'),
        ('CANCELLED', 'Cancelado'),
    ]

    client = models.CharField(max_length=200, verbose_name='Cliente')
    date = models.DateField(verbose_name='Fecha')
    due_date = models.DateField(verbose_name='Fecha de vencimiento')
    total_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto total'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Estado'
    )
    description = models.TextField(blank=True, verbose_name='Descripción')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Factura {self.id} - {self.client} - {self.total_amount}"

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-date']

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Factura'
    )
    description = models.CharField(max_length=200, verbose_name='Descripción')
    quantity = models.PositiveIntegerField(verbose_name='Cantidad')
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Precio unitario'
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
        verbose_name = 'Item de factura'
        verbose_name_plural = 'Items de factura'

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('UTILITIES', 'Servicios'),
        ('RENT', 'Alquiler'),
        ('SALARY', 'Salarios'),
        ('SUPPLIES', 'Insumos'),
        ('OTHER', 'Otros'),
    ]

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoría'
    )
    date = models.DateField(verbose_name='Fecha')
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
        return f"{self.get_category_display()} - {self.date} - {self.amount}"

    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-date']

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Usuario'
    )
    action = models.CharField(
        max_length=10,
        choices=ACTION_TYPES,
        verbose_name='Acción'
    )
    model_name = models.CharField(max_length=100, verbose_name='Modelo')
    object_id = models.PositiveIntegerField(verbose_name='ID del objeto')
    details = models.TextField(verbose_name='Detalles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.model_name}"

    class Meta:
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Registros de auditoría'
        ordering = ['-created_at']

class Report(models.Model):
    REPORT_TYPES = [
        ('INCOME', 'Ingresos'),
        ('EXPENSE', 'Gastos'),
        ('BALANCE', 'Balance'),
        ('CASH_FLOW', 'Flujo de Caja'),
    ]

    title = models.CharField(max_length=200, verbose_name='Título')
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        verbose_name='Tipo de reporte'
    )
    start_date = models.DateField(verbose_name='Fecha inicial')
    end_date = models.DateField(verbose_name='Fecha final')
    description = models.TextField(blank=True, verbose_name='Descripción')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"

    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-created_at']
