import math
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum,Q
from django.db.models.functions import Coalesce
from django.db.models import DecimalField
from django.contrib.auth.models import AbstractUser



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
    FORMAT_CHOICES = [
        ('WEB', 'Web'),
        ('XLSX', 'Excel'),
    ]
        
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
    format_type = models.CharField("Format", max_length=4, choices=FORMAT_CHOICES,default='WEB', )
    isChangeOrder = models.BooleanField(default=False)
    dataPreview = models.JSONField(default=list, null=True )

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
    
    @property
    def total_change_order(self):
        try:
            return ((self.profit_value or 0) + (self.projected_cost or 0)) - ((self.id_related_budget.profit_value or 0) + (self.id_related_budget.projected_cost or 0))
        except:
            return 0

    @property
    def id_related_total_value(self):
        try:
            return (self.id_related_budget.profit_value or 0) + (self.id_related_budget.projected_cost or 0)
        except:
            return 0 


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
    is_generated_by_checklist = models.BooleanField(default=False)
    id_generated_by_checklist = models.CharField(max_length=50, default='Null')

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
    add_post_and_hole = models.BooleanField(default=False)
    add_hole_checked = models.BooleanField(default=False)
    add_utilities_checked = models.BooleanField(default=False)
    add_removal_checked = models.BooleanField(default=False)
    totalFtAdPost = models.JSONField(default=list, null=True )
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
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor",  related_name='sales_advisor_projects')
    project_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Project Manager", related_name='project_manager_projects')
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)
    city = models.CharField("City", max_length=100, default="Hialeah")
    state = models.CharField("State/Province", max_length=100, default="Florida")
    zip_code = models.CharField("ZIP/Postal Code", max_length=20, blank=True, null=True)
    country = models.CharField("Country", max_length=100, default="United States")
    folder_id = models.CharField("Folder ID", max_length=255, null=True, blank=True)
    def __str__(self):
        return self.project_name
    
    
    def get_approved_proposal(self):
        """
        Retorna el único proposal aprobado asociado al proyecto.
        """
        return self.proposals.filter(status=ProposalProjects.STATUS_APPROVED).first()


from django.db import models
from django.utils import timezone

class InvoiceProjects(models.Model):
    STATUS_SENT = 'sent'
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_SENT, 'Sent'),                # Enviada
        (STATUS_PENDING, 'Pending'),          # Pendiente de pago
        (STATUS_PAID, 'Paid'),                # Pagada
        (STATUS_OVERDUE, 'Overdue'),          # Vencida
        (STATUS_CANCELLED, 'Cancelled'),      # Cancelada
    ]

    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='invoices')
    budget = models.ForeignKey('BudgetEstimate', on_delete=models.CASCADE, null=True, related_name='invoices')
    proposal = models.ForeignKey('ProposalProjects', on_delete=models.CASCADE, null=True, related_name='invoices')
    invoiceInfo = models.JSONField(default=dict, blank=True)
    date_created = models.DateTimeField("Date Created", default=timezone.now)
    due_date = models.DateTimeField("Due Date", null=True)
    subtotal = models.DecimalField("Subtotal", max_digits=15, decimal_places=2,default=0)  # Added subtotal
    tax = models.DecimalField("Tax", max_digits=15, decimal_places=2, default=0)  # Added tax
    retention = models.DecimalField("Retention", max_digits=15, decimal_places=2, default=0)  # Definir valor predeterminado
    total_invoice = models.DecimalField("Total Invoice", max_digits=15, decimal_places=2, default=0)
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor", blank=True)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_SENT)
    total_paid = models.DecimalField("Total Invoice Paid", max_digits=15, decimal_places=2, default=0)
    type_invoice =  models.CharField(max_length=255, default='none')
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        
    @property
    def percentage_of_proposal(self):
        if self.proposal and self.proposal.total_proposal > 0:
            return int((self.total_invoice / math.floor(self.proposal.total_proposal)) * 100)
        return 0
    
    @property
    def percentage_paid(self):
        if self.total_invoice > 0:
            return round((self.total_paid / self.total_invoice) * 100, 2)
        return 0
    

    
class ProposalProjects(models.Model):
    # Estados del invoice
    STATUS_NEW = 'new'
    STATUS_SENT = 'sent'
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),               
        (STATUS_SENT, 'Sent'),             
        (STATUS_PENDING, 'Pending'),       
        (STATUS_APPROVED, 'Approved'),    
        (STATUS_REJECTED, 'Rejected'),      
    ]
    
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='proposals')
    budget = models.ForeignKey('BudgetEstimate', on_delete=models.CASCADE, null=True, related_name='proposals')
    tracking_id = models.CharField(max_length=255)  # Unique tracking ID
    proposalInfo = models.JSONField(default=dict, blank=True)
    project_name = models.CharField(max_length=255, default='none')  # Added project name
    date_created = models.DateTimeField("Date Created", default=timezone.now)
    due_date = models.DateTimeField("Due Date",)
    subtotal = models.DecimalField("Subtotal", max_digits=15, decimal_places=2,default=0)  # Added subtotal
    tax = models.DecimalField("Tax", max_digits=15, decimal_places=2, default=0)  # Added tax
    retention = models.DecimalField("Retention", max_digits=15, decimal_places=2, default=0)  # Definir valor predeterminado
    total_proposal = models.DecimalField("Total Proposal", max_digits=15, decimal_places=2, default=0)
    approved_by = models.CharField(max_length=255,null=True, blank=True)  # Added approved by
    print_name = models.CharField(max_length=255, null=True, blank=True)  # Added print name
    signature = models.CharField(max_length=255, null=True, blank=True)  # Added signature
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor", blank=True)
    terms_conditions = models.TextField("Terms and Conditions", null=True, blank=True)  # Optional field for terms
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    billed_proposal = models.DecimalField("Total Billed", max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = "Proposal"
        verbose_name_plural = "Proposals"
        
    @property
    def remaining_amount(self):
        return self.total_proposal - self.billed_proposal


class ProjectBudgetXLSX(models.Model):
    budget = models.ForeignKey(BudgetEstimate, related_name='xlxs_data', on_delete=models.CASCADE)
    cost_items = models.JSONField("Cost Items", default=list)
    value_items = models.JSONField("Value Items", default=list)
    total_cost = models.DecimalField("Total Cost", max_digits=10, decimal_places=2, default=0)
    total_budget = models.DecimalField("Total Budget", max_digits=10, decimal_places=2, default=0)
    xlsx_id = models.CharField("Folder ID", max_length=255, null=True, blank=True)



class TaskProject(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks')
    gantt_data = models.JSONField(default=list)

    def __str__(self):
        return f"TaskProject for {self.project.project_name}"
    


class RealCostProject(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='cost_items')
    items = models.JSONField(default=list)
    total = models.CharField(max_length=255, default='none')
    
    def __str__(self):
        return f"RealCostProject for {self.project.project_name}"



from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    ROLE_TYPES = [
        ('admin', 'Administrador'),
        ('sales', 'Vendedor'),
        ('production', 'Producción'),
        ('other', 'Otro'),
    ]

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    hierarchy_level = models.PositiveIntegerField(default=1)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES, default='other')

    def __str__(self):
        return f"{self.name} (Nivel {self.hierarchy_level})"

    class Meta:
        ordering = ['hierarchy_level']


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name="users")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    # Resolviendo conflictos con `related_name`
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",  # Cambiar el related_name por uno único
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",  # Cambiar el related_name por uno único
        blank=True,
    )

    def __str__(self):
        return f"{self.username} ({self.role.name if self.role else 'Sin Rol'})"
