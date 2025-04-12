from .auth_views import home, signup, signin, closeSession, custom_404_view
from .customer_views import customers, detail_customer, edit_customer, delete_customer
from .search_views import search_customers, check_email_exists, search_projects
from .projects_views  import delete_budget, delete_invoice, changePaidInvoice, select_Manager,  view_changeOrder,chat_with_groq, pdf_proposal, new_change_order, delete_proposal, delete_project, projects, aiaInvoice10, aiaInvoice5, MdcpInvoice, BroadInvoice10, pdf_invoice,  detail_project, new_budget, view_budget, generate_pdf, view_budgetSimple, delete_budget,  edit_budget, delete_invoice
from .production_views import production, production_project, setDateInProduction, save_gantt_data, save_real_cost_by_items
from .settings_views import settings
from .metrics_views import metrics, cost_trend, project_status_distribution, sales_performance_view, projects_by_creation_date, proposals_donut_chart
from .team_views import active_users_view
