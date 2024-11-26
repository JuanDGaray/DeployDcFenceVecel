import math
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import DecimalField

class Customer(models.Model):
    # Tipos de clientes
    CUSTOMER_TYPES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('contractor', 'Contractor'),
    ]
    
    # Estados del cliente
    STATUS_NEW = 'new'
    STATUS_CONTACTED = 'contacted'
    STATUS_QUOTE_SENT = 'quote_sent'
    STATUS_IN_NEGOTIATION = 'in_negotiation'
    STATUS_APPROVED = 'approved'
    STATUS_NOT_APPROVED = 'not_approved'
    STATUS_IN_PRODUCTION = 'in_production'
    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_INACTIVE = 'inactive'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_QUOTE_SENT, 'Quote Sent'),
        (STATUS_IN_NEGOTIATION, 'In Negotiation'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_NOT_APPROVED, 'Not Approved'),
        (STATUS_IN_PRODUCTION, 'In Production'),
        (STATUS_PENDING_PAYMENT, 'Pending Payment'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # Campos del cliente
    first_name = models.CharField("First Name", max_length=100)
    last_name = models.CharField("Last Name", max_length=100)
    company_name = models.CharField("Company Name", max_length=200, blank=True, null=True)
    customer_type = models.CharField("Customer Type", max_length=20, choices=CUSTOMER_TYPES, default='individual')
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Phone", max_length=20)
    address = models.TextField("Address")
    city = models.CharField("City", max_length=100)
    state = models.CharField("State/Province", max_length=100)
    zip_code = models.CharField("ZIP/Postal Code", max_length=20, blank=True, null=True)
    country = models.CharField("Country", max_length=100)
    date_created = models.DateTimeField("Date Created", default=timezone.now)
    last_updated = models.DateTimeField("Last Updated", auto_now=True)
    is_active = models.BooleanField("Active", default=True)
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor")
    number_of_projects = models.PositiveIntegerField("Number of Projects", default=0)

    class Meta:
        ordering = ['-date_created']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        """Retorna el nombre completo o el nombre de la empresa del cliente."""
        if self.customer_type == 'company':
            return f"{self.company_name} | {self.first_name} {self.last_name}".strip() if self.first_name or self.last_name else self.company_name
        return self.get_full_name()

    def get_full_name(self):
        """Retorna el nombre completo del cliente."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_address(self):
        """Retorna la dirección completa del cliente."""
        address_parts = [self.address, self.city, self.state]
        if self.zip_code:
            address_parts.append(self.zip_code)
        address_parts.append(self.country)
        return ", ".join(filter(None, address_parts))


class BudgetEstimate(models.Model):
    STATUS_SAVED = 'saved'
    STATUS_SENT = 'sent'
    STATUS_REJECTED = 'rejected'
    STATUS_COMPLETED = 'completed'
    STATUS_OBSOLETE = 'obsolete'
    STATUS_BILLED = 'billed'

    BUDGET_STATUS_CHOICES = [
        (STATUS_SAVED, 'Saved'),
        (STATUS_SENT, 'Sent'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_OBSOLETE, 'Obsolete'),
        (STATUS_BILLED, 'Billed')
    ]
    
    id = models.AutoField(primary_key=True, verbose_name="Budget ID")
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='budget_categories')
    projected_cost = models.DecimalField("Projected Cost", max_digits=10, decimal_places=2)
    version_budget = models.IntegerField("Version Budget", default=0)
    id_related_budget = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='related_budgets'
    )
    date_created = models.DateTimeField("Date Created", default=timezone.now)
    last_updated = models.DateTimeField("Last Updated", auto_now=True)
    profit_value = models.DecimalField("Profit Value", max_digits=30, decimal_places=2, blank=False, null=False)
    actual_cost = models.DecimalField("Actual Cost", max_digits=30, decimal_places=2, blank=True, null=True)
    status = models.CharField("Status", max_length=20, choices=BUDGET_STATUS_CHOICES, default=STATUS_SAVED)
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor")
    actual_invoice = models.DecimalField("Actual Cost", max_digits=30, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Budget for {self.project.project_name}"
    
    def mark_as_obsolete(self):
        """
        Cambia el estado del presupuesto a 'Obsolete'.
        """
        self.status = self.STATUS_OBSOLETE
        self.save()
        return self
    
    @property
    def total_value(self):
        """
        Returns the sum of profit_value and projected_cost.
        """
        return (self.profit_value or 0) + (self.projected_cost or 0)
    
    @property
    def latest_version(self):
        """
        Returns the latest version of the budget related to this one.
        If there are no related versions, it returns the current budget itself.
        """
        budgets = BudgetEstimate.objects.filter(id_related_budget=self).order_by('-id')
        return budgets.first()
    
    @property
    def total_percentage_invoiced(self):
        related_invoices = self.invoices.all()  # Uso del nombre del `related_name` si lo tienes configurado
        return sum(invoice.percentage_of_budget for invoice in related_invoices)


class BudgetEstimateLaborData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Labor ID")
    budget = models.ForeignKey(BudgetEstimate, related_name='labors', on_delete=models.CASCADE)
    labor_description = models.CharField(max_length=255, blank=True)
    cost_by_day = models.DecimalField(max_digits=10, decimal_places=2)
    days = models.IntegerField()
    lead_time = models.CharField(max_length=50, blank=True)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_generated_by_utils = models.BooleanField(default=False)
    item_value = models.CharField(max_length=50, default='GENERAL')

class BudgetEstimateMaterialData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Material ID")
    budget = models.ForeignKey(BudgetEstimate, related_name='materials', on_delete=models.CASCADE)
    material_description = models.CharField(max_length=255, blank=True)
    is_generated_by_utils = models.BooleanField(default=False)
    item_value = models.CharField(max_length=50, default='GENERAL')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time = models.CharField(max_length=50, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)


class BudgetEstimateContractorData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Contractor ID")
    budget = models.ForeignKey(BudgetEstimate, related_name='contractors', on_delete=models.CASCADE)
    contractor_description = models.CharField(max_length=255)
    lead_time = models.CharField(max_length=50, blank=True)
    contractor_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_generated_by_utils = models.BooleanField(default=False)
    item_value = models.CharField(max_length=50, default='GENERAL')

class BudgetEstimateMiscData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Misc ID")
    budget = models.ForeignKey(BudgetEstimate, related_name='misc_data', on_delete=models.CASCADE)
    misc_description = models.CharField(max_length=255, blank=True)
    misc_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lead_time = models.CharField(max_length=50, blank=True)
    is_generated_by_utils = models.BooleanField(default=False)
    item_value = models.CharField(max_length=50, default='GENERAL')
    
class BudgetEstimateDeductsData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Deducts ID")
    budget = models.ForeignKey(BudgetEstimate, related_name='deducts', on_delete=models.CASCADE)
    deduct_description = models.CharField(max_length=255, blank=True)
    deduct_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lead_time = models.CharField(max_length=50, blank=True)
    is_generated_by_utils = models.BooleanField(default=False)
    item_value = models.CharField(max_length=50, default='GENERAL')

class BudgetEstimateProfitData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Profit ID")
    budget = models.ForeignKey(BudgetEstimate, related_name='profits', on_delete=models.CASCADE)
    profit_description = models.CharField(max_length=255, blank=True)
    lead_time = models.CharField(max_length=50, null=True, blank=True)
    profit_value = models.DecimalField(max_digits=10, decimal_places=2)
    is_generated_by_utils = models.BooleanField(default=False)
    item_value = models.CharField(max_length=50, default='GENERAL')

class BudgetEstimateUtil(models.Model):
    # Costos y otros datos de los agujeros
    id = models.AutoField(primary_key=True, verbose_name="Util ID")
    budget = models.ForeignKey(BudgetEstimate, related_name='util_data', on_delete=models.CASCADE)
    add_hole_checked = models.BooleanField(default=False)
    add_utilities_checked = models.BooleanField(default=False)
    add_removal_checked = models.BooleanField(default=False)
    total_ft = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_posts = models.IntegerField(default=0)
    hole_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.96)
    hole_cost = models.DecimalField(max_digits=10, decimal_places=2, default=180)
    cost_per_hole = models.DecimalField(max_digits=10, decimal_places=2, default=3)
    utilities_cost = models.DecimalField(max_digits=10, decimal_places=2, default=1.5)
    removal_cost = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    
    # Costos de manufactura
    add_unit_cost_mi = models.BooleanField(default=False)
    manufacturing_data = models.JSONField(default=list)
    cost_data = models.JSONField(default=list)

    # Costos de manufactura (MW)
    add_unit_cost_mw = models.BooleanField(default=False)
    data_unit_cost_mw = models.JSONField(default=list)
    data_unit_cost_mw_items = models.JSONField(default=list)
    add_data_profit_by_daymw = models.BooleanField(default=False)
    data_profit_by_daymw = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    

    # Información de ganancias por día
    add_data_profit_by_day = models.BooleanField(default=False)
    days = models.IntegerField(default=15)
    profit_value = models.DecimalField(max_digits=10, decimal_places=2)
    use_day_in_items_manufacturing = models.BooleanField(default=False)

    # Información de préstamos
    add_loans = models.BooleanField(default=False)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f'Util {self.id}'
    
# Modelo para representar un proyecto
class Project(models.Model):
    
    # Estados de projectos
    STATUS_NEW = 'new'
    STATUS_CONTACTED = 'contacted'
    STATUS_QUOTE_SENT = 'quote_sent'
    STATUS_IN_NEGOTIATION = 'in_negotiation'
    STATUS_APPROVED = 'approved'
    STATUS_NOT_APPROVED = 'not_approved'
    STATUS_IN_PRODUCTION = 'in_production'
    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_INACTIVE = 'inactive'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_QUOTE_SENT, 'Quote Sent'),
        (STATUS_IN_NEGOTIATION, 'In Negotiation'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_NOT_APPROVED, 'Not Approved'),
        (STATUS_IN_PRODUCTION, 'In Production'),
        (STATUS_PENDING_PAYMENT, 'Pending Payment'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.AutoField(primary_key=True, verbose_name="Project ID")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="projects", verbose_name="Customer")
    project_name = models.CharField("Project Name", max_length=255)
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    description = models.TextField("Project Description", null=True, blank=True)
    estimated_cost = models.DecimalField("Estimated Cost", max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    actual_cost = models.DecimalField("Actual Cost", max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor")
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)
    city = models.CharField("City", max_length=100, default="Hialeah")
    state = models.CharField("State/Province", max_length=100, default="Florida")
    zip_code = models.CharField("ZIP/Postal Code", max_length=20, blank=True, null=True)
    country = models.CharField("Country", max_length=100, default="United States")

    def __str__(self):
        return self.project_name
    

    def update_estimated_cost(self):
        total_estimated_cost = self.budget_categories.aggregate(
            total=Coalesce(Sum('projected_cost'), 0, output_field=DecimalField())
        )['total']
        self.estimated_cost = total_estimated_cost
        self.save()

    def update_actual_cost(self):
        total_actual_cost = self.budget_categories.aggregate(
            total=Coalesce(Sum('actual_cost'), 0, output_field=DecimalField())
        )['total']
        self.actual_cost = total_actual_cost
        self.save()
        
    def formatted_estimated_cost(self):
        return "${:,.2f}".format(self.estimated_cost) if self.estimated_cost is not None else "$0.00"

    def formatted_actual_cost(self):
        return "${:,.2f}".format(self.actual_cost) if self.actual_cost is not None else "$0.00"


from django.db import models
from django.utils import timezone

class InvoiceProjects(models.Model):
    # Estados del invoice
    STATUS_NEW = 'new'
    STATUS_SENT = 'sent'
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_PAID = 'paid'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),               
        (STATUS_SENT, 'Sent'),             
        (STATUS_PENDING, 'Pending'),       
        (STATUS_APPROVED, 'Approved'),    
        (STATUS_REJECTED, 'Rejected'),      
        (STATUS_PAID, 'Paid'),           
    ]
    
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='invoices')
    budget = models.ForeignKey('BudgetEstimate', on_delete=models.SET_NULL, null=True, related_name='invoices')
    tracking_id = models.CharField(max_length=255)  # Unique tracking ID
    invoiceInfo = models.JSONField(default=dict, blank=True)
    project_name = models.CharField(max_length=255, default='none')  # Added project name
    date_created = models.DateTimeField("Date Created", default=timezone.now)
    due_date = models.DateTimeField("Due Date",)
    subtotal = models.DecimalField("Subtotal", max_digits=15, decimal_places=2,default=0)  # Added subtotal
    tax = models.DecimalField("Tax", max_digits=15, decimal_places=2, default=0)  # Added tax
    retention = models.DecimalField("Retention", max_digits=15, decimal_places=2, default=0)  # Definir valor predeterminado
    total_invoice = models.DecimalField("Total Invoice", max_digits=15, decimal_places=2, default=0)
    approved_by = models.CharField(max_length=255,null=True, blank=True)  # Added approved by
    print_name = models.CharField(max_length=255, null=True, blank=True)  # Added print name
    signature = models.CharField(max_length=255, null=True, blank=True)  # Added signature
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor", blank=True)
    terms_conditions = models.TextField("Terms and Conditions", null=True, blank=True)  # Optional field for terms
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        
    @property
    def percentage_of_budget(self):
        if self.budget and self.budget.total_value > 0:
            return int((self.total_invoice / math.floor(self.budget.total_value)) * 100)
        return 0


@receiver(post_save, sender=BudgetEstimate)
def update_project_estimated_cost(sender, instance, **kwargs):
    instance.project.update_estimated_cost()