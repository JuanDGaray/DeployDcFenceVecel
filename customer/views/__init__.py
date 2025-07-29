from .auth_views import home, signup, signin, closeSession, custom_404_view
from .home_views import my_space
from .customer_views import (customers, detail_customer, edit_customer, delete_customer, get_client_emails, emails_sent_to_client_view,
                              send_proposal_email, reply_email, mark_email_as_read, download_email_attachment, send_invoice_email)
from .search_views import search_customers, check_email_exists, search_projects
from .projects_views  import (  delete_budget, delete_invoice, duplicate_project,create_copy_budget,
                                changePaidInvoice, select_Manager, assign_accounting_manager, assign_project_manager,
                                add_comment, view_changeOrder,chat_with_groq, pdf_proposal, new_change_order, 
                                delete_proposal, delete_project, projects, aiaInvoice10, aiaInvoice5, MdcpInvoice, 
                                updateMdcpInvoice, BroadInvoice10, view_invoice,  detail_project, new_budget, view_budget, generate_pdf,       
                                view_budgetSimple, delete_budget,  edit_budget, delete_invoice, create_project, edit_project,
                                project_history, close_project, cancel_proposal, cancel_project)

from .production_views import production, production_project, setDateInProduction, save_gantt_data, save_real_cost_by_items, update_project_production, close_production
from .settings_views import settings, add_user_post, delete_user
from .metrics_views import metrics, cost_trend, project_status_distribution, sales_performance_view, projects_by_creation_date, proposals_donut_chart
from .team_views import active_users_view
from .utils_get import *
from .planning_accounting import *


    