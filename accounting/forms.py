from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Account, Transaction, Invoice, InvoiceItem, Expense, Report

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'description', 'initial_balance']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'initial_balance': forms.NumberInput(attrs={'step': '0.01'}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'account', 'transaction_type', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'transaction_type': forms.Select(attrs={
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'right',
                'data-bs-html': 'true',
                'title': '<strong>Tipos de Transacción:</strong><br>'
                         '<strong>Crédito (+):</strong> Aumenta el saldo de la cuenta.<br>'
                         '<strong>Débito (-):</strong> Disminuye el saldo de la cuenta.<br><br>'
                         '<strong>Para cuentas de Activo:</strong><br>'
                         '- Crédito: Disminuye el activo<br>'
                         '- Débito: Aumenta el activo<br><br>'
                         '<strong>Para cuentas de Pasivo:</strong><br>'
                         '- Crédito: Aumenta el pasivo<br>'
                         '- Débito: Disminuye el pasivo<br><br>'
                         '<strong>Para cuentas de Ingreso:</strong><br>'
                         '- Crédito: Aumenta el ingreso<br>'
                         '- Débito: Disminuye el ingreso<br><br>'
                         '<strong>Para cuentas de Gasto:</strong><br>'
                         '- Crédito: Disminuye el gasto<br>'
                         '- Débito: Aumenta el gasto'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clase para inicializar los tooltips de Bootstrap
        self.fields['transaction_type'].widget.attrs['class'] = 'form-select'
        
        # Agregar JavaScript para inicializar los tooltips
        self.fields['transaction_type'].widget.attrs['onchange'] = 'updateTransactionTypeTooltip(this)'
        
        # Agregar ayuda al campo
        self.fields['transaction_type'].help_text = 'Seleccione el tipo de transacción. Pase el mouse sobre este campo para más información.'

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'date', 'due_date', 'total_amount', 'status', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'total_amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'total']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'total': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        
        if quantity and unit_price:
            cleaned_data['total'] = quantity * unit_price
        
        return cleaned_data

# Formset for invoice items
InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True
)

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'date', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'report_type', 'start_date', 'end_date', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('La fecha inicial no puede ser posterior a la fecha final.')
        
        return cleaned_data 