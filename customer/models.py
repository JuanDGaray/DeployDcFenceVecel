import math
from django.db import models
from django.utils import timezone
from datetime import date
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum,Q
from django.db.models.functions import Coalesce
from django.db.models import DecimalField
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json
from datetime import datetime
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

ACCOUNTING_COST_REQUEST_CHOICES = [
    ('GLOBAL COST REQUEST', 'GLOBAL COST REQUEST'),
    ('ITEM COST REQUEST', 'ITEM COST REQUEST'),
]


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
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

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
    hole_cost = models.DecimalField(max_digits=10, decimal_places=2, default=180)
    cost_per_hole = models.DecimalField(max_digits=10, decimal_places=2, default=3)
    utilities_cost = models.DecimalField(max_digits=10, decimal_places=2, default=1.5)
    removal_cost = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    
    # Costos de manufactura
    add_unit_cost_mi = models.BooleanField(default=False)
    manufacturing_data = models.JSONField(default=list)
    cost_data = models.JSONField(default=list)
    profit_value_installation_check = models.BooleanField(default=False)
    profit_value_installation = models.DecimalField(max_digits=10, decimal_places=2, default=140)

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

    # Información de margen de error
    margin_error_check = models.BooleanField(default=False)
    percentage_margin_error = models.IntegerField(default=5)

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
    STATUS_IN_PLANNING = 'planning_and_documentation'   
    STATUS_IN_ACCOUNTING = 'in_accounting'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_QUOTE_SENT, 'Quote Sent'),
        (STATUS_IN_NEGOTIATION, 'In Negotiation'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_NOT_APPROVED, 'Not Approved'),
        (STATUS_IN_PLANNING, 'Planning and Documentation'),
        (STATUS_IN_ACCOUNTING, 'In Accounting'),
        (STATUS_IN_PRODUCTION, 'In Production'),
        (STATUS_PENDING_PAYMENT, 'Pending Payment'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
        ]

    id = models.AutoField(primary_key=True, verbose_name="Project ID")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="projects", verbose_name="Customer")
    project_name = models.CharField("Project Name", max_length=255)
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    status = models.CharField("Status", max_length=30, choices=STATUS_CHOICES, default=STATUS_NEW)
    description = models.TextField("Project Description", null=True, blank=True)
    estimated_cost = models.DecimalField("Estimated Cost", max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    actual_cost = models.DecimalField("Actual Cost", max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    sales_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor",  related_name='sales_advisor_projects')
    project_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Project Manager", related_name='project_manager_projects')
    accounting_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Accounting Manager", related_name='accounting_manager_projects')
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)
    city = models.CharField("City", max_length=100, default="Hialeah")
    state = models.CharField("State/Province", max_length=100, default="Florida")
    zip_code = models.CharField("ZIP/Postal Code", max_length=20, blank=True, null=True)
    country = models.CharField("Country", max_length=100, default="United States")
    folder_id = models.CharField("Folder ID", max_length=255, null=True, blank=True)
    accounting_cost_request = models.CharField("Accounting Cost Request", max_length=50, choices=ACCOUNTING_COST_REQUEST_CHOICES, default=None, null=True, blank=True)
    production_funding_request = models.OneToOneField('ProductionFundingRequest', null=True, blank=True, on_delete=models.SET_NULL, related_name='project_funding')
    evidence_required = models.BooleanField(default=False, null=True, blank=True)
    production_closed = models.BooleanField(default=False, null=True, blank=True)
    production_closed_date = models.DateTimeField(null=True, blank=True, verbose_name="Production Closed Date")
    collaborators = models.ManyToManyField(User, related_name='collaborating_projects', blank=True, verbose_name="Collaborators")

    def __str__(self):
        return f"{self.project_name} - {self.customer.get_full_name()}"
    
    
    def get_approved_proposal(self):
        """     
        Retorna el único proposal aprobado asociado al proyecto.
        """
        return self.proposals.filter(status=ProposalProjects.STATUS_APPROVED).first()

    def actual_cost_usd(self):
        return f"${self.actual_cost:,.2f}" if self.actual_cost else "$0.00"
    
    def estimated_cost_usd(self):
        return f"${self.estimated_cost:,.2f}" if self.estimated_cost else "$0.00"

class ProjectDocumentRequirement(models.Model):
    TYPE_DOCUMENT_CHOICES = [
        ('Permit', 'Permit'),
        ('SOV', 'SOV'),
        ('Materials', 'Materials'),
        ('Plans/Drawings', 'Plans/Drawings'),
        ('Documents', 'Documents'),
        ('COI Insurance', 'COI Insurance'),
        ('NTC/PO', 'NTC/PO'),
        ('Contract', 'Contract'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='document_requirements')
    type_document = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    file_url = models.CharField(max_length=255, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.name}"

class commentsProject(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    mentioned_users = models.ManyToManyField(User, related_name='mentions', blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="User", blank=True)
    date_created = models.DateTimeField("Date Created", default=timezone.now)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    
    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['-date_created']
    
    def __str__(self):
        return f'Comment {self.id}'
    
    @property
    def has_replies(self):
        """Returns True if this comment has replies"""
        return self.replies.exists()
    
    @property
    def is_reply(self):
        """Returns True if this comment is a reply to another comment"""
        return self.parent_comment is not None

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

class PaymentsReceived(models.Model):
    invoice = models.ForeignKey(InvoiceProjects, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor", blank=True)
    payment_method = models.CharField(max_length=255, null=True, blank=True)
    id_transaction = models.CharField(max_length=255, null=True, blank=True)
    url_receipt = models.CharField(max_length=255, null=True, blank=True)
    
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
    budget = models.ForeignKey(BudgetEstimate, on_delete=models.CASCADE, null=True, related_name='proposals')
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
    terms_conditions = models.TextField("Terms and Conditions", null=True, blank=True)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    billed_proposal = models.DecimalField("Total Billed", max_digits=15, decimal_places=2, default=0)
    exclusions = models.TextField("Exclusions", null=True, blank=True, default="Permit Fee and processing, Site survey, Electrical fence grounding")
    scope_prices = models.JSONField("Scope Prices", default=dict, blank=True)  # Campo para almacenar los precios por scope

    class Meta:
        verbose_name = "Proposal"
        verbose_name_plural = "Proposals"
        
    @property
    def remaining_amount(self):
        return max(0, self.total_proposal - self.billed_proposal)

    @property
    def is_overdue(self):
        return self.due_date and self.due_date.date() < date.today() and self.status not in ['approved', 'rejected']

    @property
    def is_today(self):
        return self.due_date and self.due_date.date() == date.today() and self.status not in ['approved', 'rejected']


    @property
    def billing_progress(self):
        if self.total_proposal > 0:
            return round((self.billed_proposal / self.total_proposal) * 100, 2)
        return 0.0

    @property
    def days_until_due(self):
        return (self.due_date.date() - date.today()).days if self.due_date else None

    @property
    def is_fully_billed(self):
        return self.remaining_amount == 0

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, "Unknown")

    @property
    def calculated_tax(self):
        TAX_RATE = 0.15  # Example: 15%
        return round(self.subtotal * TAX_RATE, 2)

    @property
    def calculated_retention(self):
        RETENTION_RATE = 0.05  # Example: 5%
        return round(self.subtotal * RETENTION_RATE, 2)

    @property
    def proposal_duration(self):
        if self.date_created and self.due_date:
            return (self.due_date.date() - self.date_created.date()).days
        return None


    @property
    def proposal_summary(self):
        return f"Project: {self.project_name} | Total: ${self.total_proposal} | Status: {self.status_label}"
    
    @property
    def creation_duration(self):
        """ Devuelve el número de días transcurridos desde la creación de la propuesta """
        current_time = timezone.now()
        
        # Asegúrate de que la fecha de creación también sea aware
        if self.date_created.tzinfo is None:
            self.date_created = timezone.make_aware(self.date_created, timezone.get_current_timezone())

        time_elapsed = current_time - self.date_created
        return time_elapsed.days

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
    evidence_url = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"RealCostProject for {self.project.project_name}"



class ProjectHistory(models.Model):
    """
    Modelo para registrar el historial de cambios en los proyectos.
    Guarda información sobre quién realizó el cambio, cuándo, qué se modificó y otros detalles.
    """
    # Tipos de acciones que se pueden registrar
    ACTION_TYPES = [
        ('CREATE', 'Creation'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Deletion'),
        ('STATUS_CHANGE', 'Status Change'),
        ('BUDGET_CHANGE', 'Budget Change'),
        ('PROPOSAL_CHANGE', 'Proposal Change'),
        ('INVOICE_CHANGE', 'Invoice Change'),
        ('COMMENT', 'Comment'),
        ('OTHER', 'Other'),
    ]
    
    # Campos del modelo
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='history', verbose_name="Proyecto")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    action = models.CharField("Acción", max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField("Fecha y Hora", auto_now_add=True)
    description = models.TextField("Descripción", blank=True)
    
    # Campos para almacenar información sobre el objeto modificado
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Campo para almacenar los cambios realizados (antes y después)
    changes = models.JSONField("Cambios", default=dict, blank=True)
    
    class Meta:
        verbose_name = "Historial de Proyecto"
        verbose_name_plural = "Historial de Proyectos"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.project.project_name} - {self.get_action_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def log_change(cls, project, user, action, description="", content_object=None, changes=None):
        """
        Método de clase para facilitar el registro de cambios en el historial.
        
        Args:
            project: Instancia del proyecto
            user: Usuario que realiza la acción
            action: Tipo de acción (CREATE, UPDATE, etc.)
            description: Descripción textual del cambio
            content_object: Objeto relacionado que fue modificado (opcional)
            changes: Diccionario con los cambios realizados (opcional)
        """
        history = cls(
            project=project,
            user=user,
            action=action,
            description=description,
            changes=changes or {}
        )
        
        if content_object:
            history.content_type = ContentType.objects.get_for_model(content_object)
            history.object_id = content_object.id
        
        history.save()
        return history

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('mention', 'Mention'),
        ('reply', 'Reply'),
        ('project_update', 'Project Update'),
        ('status_change', 'Status Change'),
        ('manager_assignment', 'Manager Assignment'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='notifications')
    comment = models.ForeignKey(commentsProject, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        ordering = ['-date_created']
    
    def __str__(self):
        return f'Notification for {self.recipient.username} - {self.notification_type}'

class ProductionFundingRequest(models.Model):
    project = models.OneToOneField('Project', on_delete=models.CASCADE, related_name='funding_request')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    cost_request_type = models.CharField("Cost Request Type", max_length=50, choices=ACCOUNTING_COST_REQUEST_CHOICES, null=True, blank=True)

class ProductionChangeLog(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='production_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)  # Ej: "update_cost", "add_task", "change_status"
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    data_before = models.JSONField(null=True, blank=True)
    data_after = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.project} - {self.action} - {self.timestamp:%Y-%m-%d %H:%M}"

class EmailTracking(models.Model):
    """
    Modelo para tracking de emails enviados
    """
    TRACKING_TYPES = [
        ('proposal', 'Proposal'),
        ('invoice', 'Invoice'),
        ('notification', 'Notification'),
        ('other', 'Other'),
    ]
    
    # Información del email
    tracking_id = models.CharField(max_length=255, unique=True, verbose_name="Tracking ID")
    email_type = models.CharField(max_length=20, choices=TRACKING_TYPES, verbose_name="Email Type")
    recipient_email = models.EmailField(verbose_name="Recipient Email")
    subject = models.CharField(max_length=255, verbose_name="Subject")
    
    # Relaciones
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Project")
    proposal = models.ForeignKey('ProposalProjects', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Proposal")
    invoice = models.ForeignKey('InvoiceProjects', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Invoice")
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sent By")
    
    # Tracking
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Sent At")
    opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Opened At")
    opened_count = models.PositiveIntegerField(default=0, verbose_name="Times Opened")
    last_opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Last Opened At")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    
    # Información adicional
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Additional Data")
    
    class Meta:
        verbose_name = "Email Tracking"
        verbose_name_plural = "Email Tracking"
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['tracking_id']),
            models.Index(fields=['email_type']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.email_type} - {self.recipient_email} ({self.tracking_id})"
    
    @property
    def is_opened(self):
        """Retorna True si el email ha sido abierto al menos una vez"""
        return self.opened_count > 0
    
    @property
    def days_since_sent(self):
        """Retorna los días transcurridos desde que se envió el email"""
        from django.utils import timezone
        return (timezone.now() - self.sent_at).days
    
    def mark_as_opened(self, ip_address=None, user_agent=None):
        """Marca el email como abierto y actualiza las estadísticas"""
        from django.utils import timezone
        now = timezone.now()
        
        self.opened_count += 1
        self.last_opened_at = now
        
        # Solo actualizar opened_at la primera vez
        if not self.opened_at:
            self.opened_at = now
        
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
            
        self.save()


from django.db import models

class ChangeOrderDetail(models.Model):
    budget = models.OneToOneField('BudgetEstimate', on_delete=models.CASCADE, related_name='change_order_detail')
    sub_contract_no = models.CharField(max_length=50, blank=True, null=True)
    job_location = models.CharField(max_length=255, blank=True, null=True)
    purchase_order = models.CharField(max_length=50, blank=True, null=True)
    existing_contract_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    change_order_no = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Change Order for Budget {self.budget.id}"

class ChangeOrderItem(models.Model):
    change_order = models.ForeignKey(ChangeOrderDetail, on_delete=models.CASCADE, related_name='items')
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Item for Change Order {self.change_order.id}: {self.description[:30]}"

class UserTask(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-priority', 'due_date']
        verbose_name = 'User Task'
        verbose_name_plural = 'User Tasks'
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'completed'
    
    @property
    def is_due_soon(self):
        return self.due_date <= timezone.now().date() + timedelta(days=2) and self.status != 'completed'

class CostItemDescription(models.Model):
    """
    Modelo para almacenar descripciones editables de elementos individuales de costos.
    Permite que los usuarios modifiquen las descripciones de elementos específicos
    (como "Fabrication" en Labor, "Steel Posts" en Materials) sin afectar el presupuesto.
    """
    CATEGORY_CHOICES = [
        ('materials', 'Materials'),
        ('labor', 'Labor'),
        ('contractors', 'Contractors'),
        ('utilities', 'Utilities'),
        ('overhead', 'Overhead'),
        ('miscellaneous', 'Miscellaneous'),
        ('deducts', 'Deducts'),
        ('profit', 'Profit'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    original_description = models.CharField(max_length=255, help_text="Descripción original del elemento")
    custom_description = models.CharField(max_length=255, help_text="Descripción personalizada del elemento")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Cost Item Description"
        verbose_name_plural = "Cost Item Descriptions"
        ordering = ['category', 'original_description']
        unique_together = ['category', 'original_description']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.original_description}"
    
    @classmethod
    def get_custom_description(cls, category, original_description):
        """Retorna la descripción personalizada para un elemento específico"""
        try:
            item = cls.objects.get(
                category=category,
                original_description=original_description,
                is_active=True
            )
            return item.custom_description
        except cls.DoesNotExist:
            return original_description
    
    @classmethod
    def set_custom_description(cls, category, original_description, custom_description, user=None):
        """
        Establece una descripción personalizada para un elemento de costo.
        """
        obj, created = cls.objects.get_or_create(
            category=category,
            original_description=original_description,
            defaults={'custom_description': custom_description, 'updated_by': user}
        )
        if not created:
            obj.custom_description = custom_description
            obj.updated_by = user
            obj.save()
        return obj


class ProjectCollaborationRequest(models.Model):
    """
    Modelo para manejar las solicitudes de colaboración en proyectos.
    Permite a usuarios solicitar acceso a proyectos de otros usuarios.
    """
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='collaboration_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaboration_requests_sent')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaboration_requests_received')
    message = models.TextField("Message", blank=True, help_text="Optional message explaining why you want to collaborate")
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    response_message = models.TextField("Response Message", blank=True, help_text="Optional response message from project owner")
    
    class Meta:
        verbose_name = "Project Collaboration Request"
        verbose_name_plural = "Project Collaboration Requests"
        ordering = ['-date_created']
        unique_together = ['project', 'requester']
    
    def __str__(self):
        return f"Collaboration request from {self.requester.get_full_name()} for {self.project.project_name}"
    
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING
    
    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED
    
    @property
    def is_rejected(self):
        return self.status == self.STATUS_REJECTED