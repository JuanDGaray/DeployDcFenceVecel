# Generated by Django 5.1.3 on 2025-04-08 05:24

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('account_type', models.CharField(choices=[('ASSET', 'Activo'), ('LIABILITY', 'Pasivo'), ('EQUITY', 'Capital'), ('INCOME', 'Ingreso'), ('EXPENSE', 'Gasto')], max_length=20, verbose_name='Tipo de cuenta')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('initial_balance', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Saldo inicial')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Cuenta',
                'verbose_name_plural': 'Cuentas',
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATE', 'Crear'), ('UPDATE', 'Actualizar'), ('DELETE', 'Eliminar')], max_length=10, verbose_name='Acción')),
                ('model_name', models.CharField(max_length=100, verbose_name='Modelo')),
                ('object_id', models.PositiveIntegerField(verbose_name='ID del objeto')),
                ('details', models.TextField(verbose_name='Detalles')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Registro de auditoría',
                'verbose_name_plural': 'Registros de auditoría',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('UTILITIES', 'Servicios'), ('RENT', 'Alquiler'), ('SALARY', 'Salarios'), ('SUPPLIES', 'Insumos'), ('OTHER', 'Otros')], max_length=20, verbose_name='Categoría')),
                ('date', models.DateField(verbose_name='Fecha')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Monto')),
                ('description', models.TextField(verbose_name='Descripción')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
            ],
            options={
                'verbose_name': 'Gasto',
                'verbose_name_plural': 'Gastos',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client', models.CharField(max_length=200, verbose_name='Cliente')),
                ('date', models.DateField(verbose_name='Fecha')),
                ('due_date', models.DateField(verbose_name='Fecha de vencimiento')),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Monto total')),
                ('status', models.CharField(choices=[('PENDING', 'Pendiente'), ('PAID', 'Pagado'), ('CANCELLED', 'Cancelado')], default='PENDING', max_length=20, verbose_name='Estado')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
            ],
            options={
                'verbose_name': 'Factura',
                'verbose_name_plural': 'Facturas',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=200, verbose_name='Descripción')),
                ('quantity', models.PositiveIntegerField(verbose_name='Cantidad')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Precio unitario')),
                ('total', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Total')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='accounting.invoice', verbose_name='Factura')),
            ],
            options={
                'verbose_name': 'Item de factura',
                'verbose_name_plural': 'Items de factura',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Fecha')),
                ('transaction_type', models.CharField(choices=[('CREDIT', 'Crédito'), ('DEBIT', 'Débito')], max_length=10, verbose_name='Tipo de transacción')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Monto')),
                ('description', models.TextField(verbose_name='Descripción')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='accounting.account', verbose_name='Cuenta')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
            ],
            options={
                'verbose_name': 'Transacción',
                'verbose_name_plural': 'Transacciones',
                'ordering': ['-date', '-created_at'],
            },
        ),
    ]
