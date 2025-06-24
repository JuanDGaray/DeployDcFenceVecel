from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from accounting.models import Transaction, Account
from accounting.forms import TransactionForm


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
