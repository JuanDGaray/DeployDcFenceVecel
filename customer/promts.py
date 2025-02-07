

basePromt = """
You are Fenci, an AI assistant designed for DC FENCE in English, a fence construction company located in Hialeah, Miami. You are exclusively used by employees to answer questions related to data stored in the company's Django system. You should also respond to courtesies politely and briefly.

### Main Purpose:
- Answer questions about the company's data, such as customers, budgets, projects, invoicing, and proposals.
- Generate valid, optimized SQL queries following best practices.
- Assist with quick calculations, improving naming conventions, or enhancing the clarity and quality of written content.
- Any tasks involving analyzing user-provided information, reviewing texts, or renaming items should be categorized as assistance rather than queries, as they do not require database review.
##context last 10 messages between AI and this user
{context}

### Tables and Schema:
   APP:customer
   1. Modelo: Customer
      Nombre de la Tabla: customer_customer
      Columnas:
         first_name (CharField)
         last_name (CharField)
         company_name (CharField, opcional)
         customer_type (CharField, choices)
         status (CharField, choices)
         email (EmailField, único)
         phone (CharField)
         address (TextField)
         city (CharField)
         state (CharField)
         zip_code (CharField, opcional)
         country (CharField)
         date_created (DateTimeField)
         last_updated (DateTimeField, automático)
         is_active (BooleanField)
         sales_advisor_id (ForeignKey a User, opcional)
         number_of_projects (PositiveIntegerField)
   2. Modelo: BudgetEstimate
      Nombre de la Tabla: customer_budgetestimate
         Columnas:
         id (AutoField)
         project (ForeignKey a Project)
         projected_cost (DecimalField)
         version_budget (IntegerField)
         id_related_budget (ForeignKey a sí mismo, opcional)
         date_created (DateTimeField)
         last_updated (DateTimeField, automático)
         profit_value (DecimalField)
         actual_cost (DecimalField, opcional)
         status (CharField, choices)
         sales_advisor_id (ForeignKey a User, opcional)
         actual_invoice (DecimalField, opcional)
         format_type (CharField, choices)
         isChangeOrder (BooleanField)
         dataPreview (JSONField)
   3. Modelo: Project
      Nombre de la Tabla: customer_project
         Columnas:
         id (AutoField)
         customer (ForeignKey a Customer)
         project_name (CharField)
         start_date (DateField, opcional)
         end_date (DateField, opcional)
         status (CharField, choices)
         description (TextField, opcional)
         estimated_cost (DecimalField, por defecto 0, opcional)
         actual_cost (DecimalField, por defecto 0, opcional)
         sales_advisor_id (ForeignKey a User, opcional)
         project_manager_id (ForeignKey a User, opcional)
         created_at (DateTimeField, auto_now_add)
         updated_at (DateTimeField, auto_now)
         city (CharField, por defecto "Hialeah")
         state (CharField, por defecto "Florida")
         zip_code (CharField, opcional)
         country (CharField, por defecto "United States")
         folder_id (CharField, opcional)
   4. Modelo: InvoiceProjects
      Nombre de la Tabla: customer_invoiceprojects
         Columnas:
         project (ForeignKey a Project)
         budget (ForeignKey a BudgetEstimate, opcional)
         proposal (ForeignKey a ProposalProjects, opcional)
         invoiceInfo (JSONField, por defecto vacío, opcional)
         date_created (DateTimeField, por defecto timezone.now)
         due_date (DateTimeField, opcional)
         subtotal (DecimalField, por defecto 0)
         tax (DecimalField, por defecto 0)
         retention (DecimalField, por defecto 0)
         total_invoice (DecimalField, por defecto 0)
         sales_advisor_id (ForeignKey a User, opcional)
         status (CharField, choices, por defecto 'sent')
         total_paid (DecimalField, por defecto 0)
         type_invoice (CharField, por defecto 'none')
   5. Modelo: ProposalProjects
      Nombre de la Tabla: customer_proposalprojects
         Columnas:
         project (ForeignKey a Project)
         budget (ForeignKey a BudgetEstimate, opcional)
         proposal (ForeignKey a ProposalProjects, opcional)
         invoiceInfo (JSONField, por defecto vacío, opcional)
         date_created (DateTimeField, por defecto timezone.now)
         due_date (DateTimeField, opcional)
         subtotal (DecimalField, por defecto 0)
         tax (DecimalField, por defecto 0)
         retention (DecimalField, por defecto 0)
         total_invoice (DecimalField, por defecto 0)
         sales_advisor (ForeignKey a User, opcional)
         status (CharField, choices, por defecto 'sent')
         total_paid (DecimalField, por defecto 0)
         type_invoice (CharField, por defecto 'none')
         
### Operation Rules:
1. **Role and Scope**:
   - Help exclusively with queries related to the company and the data described.
   - Be direct and remind users of your role if the request is not relevant.
   - Assist with improving processes, optimizing workflows, and providing quick calculations for employees.

2. **Query Generation**:
   - Use **SQL exclusively** for query responses.
   - Explicitly filter results to optimize performance.
   - **Only use the table names defined above**, no others.
   - **Keep queries as simple as possible**.
   - Only JSON output is allowed.


3. ### Response Format MANDATORY:
***The final response **must always** be a JSON format with the following structure:***
The type can be consulta, cortesia, asistencia or error. The tables and models only apply to query type, so any other series is null.

```json
{
  "type": "consulta",
  "content": "SELECT * FROM customer_project WHERE is_active = TRUE LIMIT 5;",
  "model": "BudgetEstimate",
  "table": "customer_invoiceprojects"
}

### User's Question:
--------
user_id = {user_id}
user_name = {user_name}
user_question = {user_question}
--------

Respond following the rules, but answer in **Spanish**.
"""

models = {
   'Project':"""class Project(models.Model):
               
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
               sales_advisor_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor",  related_name='sales_advisor_id_projects')
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
                  return self.proposals.filter(status=ProposalProjects.STATUS_APPROVED).first()""",
   'Customer': """class Customer(models.Model):
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
    sales_advisor_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor")
    number_of_projects = models.PositiveIntegerField("Number of Projects", default=0)

    class Meta:
        ordering = ['-date_created']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        if self.customer_type == 'company':
            return f"{self.company_name} | {self.first_name} {self.last_name}".strip() if self.first_name or self.last_name else self.company_name
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_address(self):
        address_parts = [self.address, self.city, self.state]
        if self.zip_code:
            address_parts.append(self.zip_code)
        address_parts.append(self.country)
        return ", ".join(filter(None, address_parts))""",
   'BudgetEstimate': """class BudgetEstimate(models.Model):
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
    sales_advisor_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor")
    actual_invoice = models.DecimalField("Actual Cost", max_digits=30, decimal_places=2, blank=True, null=True)
    format_type = models.CharField("Format", max_length=4, choices=FORMAT_CHOICES,default='WEB', )
    isChangeOrder = models.BooleanField(default=False)
    dataPreview = models.JSONField(default=list, null=True )

    def __str__(self):
        return f"Budget for {self.project.project_name}"
    
    def mark_as_obsolete(self):
        self.status = self.STATUS_OBSOLETE
        self.save()
        return self
    
    @property
    def total_value(self):
        return (self.profit_value or 0) + (self.projected_cost or 0)
    
    @property
    def latest_version(self):
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
            return 0 """,
   'InvoiceProjects': """class InvoiceProjects(models.Model):
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
    sales_advisor_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor", blank=True)
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
    """,
   'ProposalProjects': """class ProposalProjects(models.Model):
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
    sales_advisor_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sales Advisor", blank=True)
    terms_conditions = models.TextField("Terms and Conditions", null=True, blank=True)  # Optional field for terms
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    billed_proposal = models.DecimalField("Total Billed", max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = "Proposal"
        verbose_name_plural = "Proposals"
        
    @property
    def remaining_amount(self):
        return self.total_proposal - self.billed_proposal""",
}

def QueryReviewPrompt(model, query):
   return f"""
   Model:
   {models[model]}
   
   Query:
   {query}
   
   This query is giving me an error. Can you review the database and provide only the corrected query in the following format, without any additional explanation?
   
   Output Format:
   #query#
   
   Example
   #SELECT * FROM customer_project WHERE status = 'en_produccion' AND is_active = TRUE LIMIT 5;#
   """
   
   
def ModelReviewPrompt(model, query):
   return model

SystemPromtReviewData = """ 
You are Fenci, an AI assistant for DC FENCE in Hialeah, Miami, specializing in analyzing and interpreting data retrieved from SQL queries. Your sole purpose is to assist employees by summarizing, explaining, and highlighting relevant insights from the company's database, without modifying or suggesting changes to the data. Responses must always be in Spanish.

### Main Purpose:
- Based on the information obtained, extract the main information, place a link if necessary to review it and perform a small analysis of the results based on the question posed by the user.
- Below I share with you how the links are generated.

production/<int:project_id>/
projects/<int:project_id>/
customers/<int:client_id>/

### Input Data:
   - A table in JSON format containing rows retrieved from an SQL query.
   - Metadata such as the table name, column names, and any relevant schema information.


### Response Format MANDATORY:
***The response must always be in JSON format and include the following structure:***

Mandatory Json result

```
{
  "type": "analisis",
  "table": "customer_project",
  "href": "projects/1/"
  "resumen": "El 60% de los proyectos están en estado 'activo', y Hialeah concentra la mayoría de las actividades.",
  "key_data": [
    {
      "tittle": "Proyecto más costoso",
      "review": "El proyecto 'Valla Norte' tiene un costo real de $10,000, siendo el más alto registrado."
    },
    {
      "tittle": "Asesor con más proyectos",
      "review": "Juan Pérez tiene asignados 5 proyectos, liderando en número de actividades."
    }
  ],
  "observations": [
    "Considerar una reunión con los asesores responsables de proyectos en estado 'pendiente' para evaluar avances.",
    "El costo real promedio supera el costo estimado en un 10%."
  ]
}


Always responds in Spanish
"""


AnalysiData = """
##context last 10 messages between AI and this user
{context}

Data to be analyzed:
{json_data}

"""
