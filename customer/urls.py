from django import utils
from django.urls import path
from . import views
from .views.production_views import request_cost_by_pm, assign_cost_by_accounting
from .views.customer_views import download_email_attachment

urlpatterns = [
    path('attachment_download/', download_email_attachment, name='attachment_download'),
    path('get_proposals/<int:page>/', views.utils_get.get_proposals, name='get_proposals'),
    path('get_userInfo/<int:id_user>/', views.utils_get.get_userInfo, name='get_userInfo'),
    path('get_user_info/', views.utils_get.get_userInfo, name='get_user_info'),
    path('get_projects/<int:page>/', views.utils_get.get_projects, name='get_projects'),
    path('duplicate_project/<int:project_id>/<int:customer_id>/', views.duplicate_project, name='duplicate_project'),
    path('create_copy_budget/<int:original_budget_id>/<int:project_id>/', views.create_copy_budget, name='create_copy_budget'),
    path('get_projects/', views.utils_get.get_projects, name='get_projects'),
    path('get_project_quick_info/<int:project_id>/', views.utils_get.get_projects_quick_info, name='get_project_quick_info'),
    path('get_proposal_quick_info/<int:proposal_id>/', views.utils_get.get_proposal_quick_info, name='get_proposal_quick_info'),
    path('update_proposal_status/<int:proposal_id>/', views.utils_get.update_proposal_status, name='update_proposal_status'),\
    path('get_array_projects/', views.utils_get.get_array_projects, name='get_array_projects'),
    path('get_notifications/', views.utils_get.get_notifications, name='get_notifications'),
    path('extend_due_date/<int:proposal_id>/', views.utils_get.extend_due_date, name='extend_due_date'), # Extend due date for a proposal
    path('get_customer/', views.utils_get.get_customer, name='get_customer'),
    path('create_new_invoice_by_project_id/<int:project_id>/', views.utils_get.create_new_invoice_by_project_id, name='create_new_invoice_by_project_id'),
    path('get_invoices/<int:page>/', views.utils_get.get_invoices, name='get_invoices'),    
    path('update_invoice_status/<int:invoice_id>/', views.utils_get.update_invoice_status, name='update_invoice_status'),
    path('get_customers_primary_info/', views.utils_get.get_customers_primary_info, name='get_customers_primary_info'),
    path('get_documents_checklist/<int:project_id>/', views.utils_get.get_documents_checklist, name='get_documents_checklist'),
    path('save_document_checklist/', views.planning_accounting.save_document_checklist, name='save_document_checklist'),
    path('update_document_checklist/', views.planning_accounting.update_document_checklist, name='update_document_checklist'),
    path('delete_document_checklist/', views.planning_accounting.delete_document_checklist, name='delete_document_checklist'),
    path('send_to_production/', views.utils_get.send_to_production, name='send_to_production'),
    path('request_cost_by_pm/<int:project_id>/', request_cost_by_pm, name='request_cost_by_pm'),
    path('assign_cost_by_accounting/<int:project_id>/', assign_cost_by_accounting, name='assign_cost_by_accounting'),
    path('get_client_emails/', views.get_client_emails, name='get_client_emails'),
    path('emails_sent_to_client/<int:project_id>/', views.emails_sent_to_client_view, name='emails_sent_to_client'),
    path('send_proposal_email/<int:project_id>/<int:proposal_id>/', views.send_proposal_email, name='send_proposal_email'),
    path('reply_email/', views.reply_email, name='reply_email'),
    path('mark_email_as_read/', views.mark_email_as_read, name='mark_email_as_read'),
]   
