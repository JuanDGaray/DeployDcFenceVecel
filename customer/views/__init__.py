from .auth_views import home, signup, signin, closeSession, custom_404_view
from .customer_views import customers, detail_customer, edit_customer, delete_customer
from .search_views import search_customers, check_email_exists, search_projects
from .projects_views  import delete_budget, delete_invoice, changePaidInvoice, select_Manager,  view_changeOrder, pdf_proposal, new_change_order, delete_proposal, delete_project, projects, aiaInvoice10, aiaInvoice5, MdcpInvoice, BroadInvoice10, pdf_invoice,  detail_project, new_budget, view_budget, generate_pdf, view_budgetSimple, delete_budget,  edit_budget, delete_invoice
from .production_views import production, production_project, setDateInProduction, save_gantt_data