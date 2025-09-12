"""
URL configuration for dcfence project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from ctypes import util
from django.urls import path, include, re_path
from customer import views
from customer.views.settings_views import settings as settings_view
from django.contrib import admin
from django.conf import settings as django_settings
from django.conf.urls.static import static
from django.conf.urls import handler404
from customer import utils
from customer.views.projects_views import project_history
from customer.views.production_views import close_production


handler404 = views.custom_404_view

urlpatterns = [
    path('', views.home, name='home'),
    path('accounting/', include('accounting.urls')), 
    path('', include('customer.urls')), 
    path('analytics/', include('analytics.urls')),
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    re_path(r'^home(/(?P<focus>\w+))?/$', views.my_space, name='home'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.closeSession, name='logout'),
    path('customers/', views.customers, name='customers'),
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.create_project, name='create_project'),
    path('production/', views.production, name='production'),
    path('production/<int:project_id>', views.production_project, name='production_project'),
    path('projects/<int:project_id>/', views.detail_project, name='detail_project'),
    path('projects/<int:project_id>/new_budget/', views.new_budget, name='new_budget'),
    path('projects/<int:project_id>/delete_project/<str:folder_root_value>/', views.delete_project, name='delete_project'),
    path('projects/<int:project_id>/delete_project/', views.delete_project, name='delete_project'),
    path('projects/<int:project_id>/view_budget/<int:budget_id>', views.view_budget, name='view_budget'),
    path('projects/<int:project_id>/edit_budget/<int:budget_id>', views.edit_budget, name='edit_budget'),
    path('projects/<int:project_id>/delete_budget/<int:budget_id>', views.delete_budget, name='delete_budget'),
    path('projects/<int:project_id>/delete_invoice/<int:invoice_id>', views.delete_invoice, name='delete_invoice'),
    path('projects/<int:project_id>/delete_proposal/<int:proposal_id>', views.delete_proposal, name='delete_proposal'),
    path('projects/<int:project_id>/view_budgetSimple/<int:budget_id>', views.view_budgetSimple, name='view_budgetSimple'),
    path('projects/<int:project_id>/edit_budgetSimple/<int:budget_id>/<int:proposal_id>', views.view_budgetSimple, name='edit_budgetSimple'),
    path('project/<int:project_id>/view_budget/<int:budget_id>/budgetPrint', views.generate_pdf, name='budget_pdf'),
    path('projects/<int:project_id>/view_invoice/<int:invoice_id>', views.view_invoice, name='view_invoice'),    
    path('projects/<int:project_id>/pdf_proposal/<int:proposal_id>', views.pdf_proposal, name='pdf_proposal'),
    path('projects/<int:project_id>/cost_breakdown/<int:proposal_id>', views.cost_breakdown, name='cost_breakdown'),
    path('projects/<int:project_id>/aiaInvoice5/<int:invoice_id>', views.aiaInvoice5, name='aiaInvoice5'),
    path('projects/<int:project_id>/new_aia5_xlxs_template/search/',  utils.new_aia5_xlxs_template, name='new_aia5_xlxs_template'),
    path('projects/<int:project_id>/new_aia10_xlxs_template/search/',  utils.new_aia10_xlxs_template, name='new_aia10_xlxs_template'),
    path('projects/<int:project_id>/aiaInvoice10/<int:invoice_id>', views.aiaInvoice10, name='aiaInvoice10'),
    path('projects/<int:project_id>/mdcpInvoice/<int:invoice_id>', views.MdcpInvoice, name='mdcpInvoice'),
    path('projects/<int:project_id>/updateMdcpInvoice/<int:invoice_id>', views.updateMdcpInvoice, name='updateMdcpInvoice'), 
    path('projects/<int:project_id>/changePaidInvoice/<int:invoice_id>', views.changePaidInvoice, name='changePaidInvoice'), 
    path('projects/<int:project_id>/broadInvoice10/<int:invoice_id>', views.BroadInvoice10, name='broadInvoice10'), 
    path('projects/<int:project_id>/gcBroDadeInvoice/<int:invoice_id>', views.GcBroDadeInvoice, name='gcBroDadeInvoice'), 
    path('customers/<int:client_id>/', views.detail_customer, name='detail_customer'),
    path('customers/edit/<int:client_id>/', views.edit_customer, name='edit_customer'),
    path('customers/<int:client_id>/delete/', views.delete_customer, name='delete_customer'),
    path('search_customers/', views.search_customers, name='search_customers'),
    path('search_projects/', views.search_projects, name='search_projects'),
    path('check-email/', views.check_email_exists, name='check_email'),
    path('projects/<int:project_id>/selectManager/', views.select_Manager, name='select_manager'),
    path('projects/<int:project_id>/assign_accounting_manager/<int:manager_id>/', views.assign_accounting_manager, name='assign_accounting_manager'),
    path('projects/<int:project_id>/assign_project_manager/<int:manager_id>/', views.assign_project_manager, name='assign_project_manager'),
    path('projects/<int:project_id>/add_comment/', views.add_comment, name='add_comment'),
    path('projects/<int:project_id>/edit_project/', views.edit_project, name='edit_project'),
    path('projects/create-folder/', utils.create_folder_in_drive, name='create_folder_in_drive'),
    path('projects/rename-folder/', utils.rename_folder_in_drive, name='rename_folder_in_drive'),
    path('projects/upload-file/', utils.upload_file_to_drive, name='upload_file_to_drive'),
    path('projects/get-folder/', utils.get_folders_in_drive, name='get_folders_in_drive'),
    path('projects/get-files/<str:folder_id>', utils.fetch_children, name='get_files'),
    path('projects/delete-file/', utils.delete_file_to_drive, name='delete_file'),
    path('projects/<int:project_id>/new_change_order/<int:proposal_id>', views.new_change_order, name='new_change_order'),
    path('projects/<int:project_id>/view_changeOrder/<int:budget_id>', views.view_changeOrder, name='view_changeOrder'),
    path('production/<int:project_id>/set_date_project/<str:start_date>/<str:end_date>/', views.setDateInProduction, name='set_date_project'),
    path('production/<int:project_id>/save_gantt_data/', views.save_gantt_data, name='save_gantt_data'),
    path('production/<int:project_id>/update_project_production/', views.update_project_production, name='update_project_production'),
    path('production/<int:project_id>/save_real_cost_by_items/', views.save_real_cost_by_items, name='save_real_cost_by_items'),
    path('production/<int:project_id>/close_production/', views.close_production, name='close_production'),
    path('api/chat/', views.chat_with_groq, name='chat_with_groq'),
    path('settings/', settings_view, name='settings'),
    path('add_user/', views.add_user_post, name='add_user'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('metrics/', views.metrics, name='metrics'),
    path('metrics/cost-trend/',views.cost_trend, name='cost_trend'),
    path('metrics/project-status-distribution/',views.project_status_distribution, name='project_status_distribution'),
    path('sales-performance/', views.sales_performance_view, name='sales_performance'),
    path('metrics/projects-by-creation-date/', views.projects_by_creation_date, name='projects_by_creation_date'),
    path('metrics/proposals_donut_chart/', views.proposals_donut_chart, name='proposals_donut_chart'),
    path('project/<int:project_id>/history/', project_history, name='project_history'), 
    path('active_users/', views.active_users_view, name='active_users'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('projects/<int:project_id>/get_activity_and_comments/', views.get_activity_project_and_comments, name='get_activity_project_and_comments'),
    path('get_users_for_mentions/', views.get_users_for_mentions, name='get_users_for_mentions'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/delete_all/', views.delete_all_notifications, name='delete_all_notifications'),
    path('send_invoice_email/<int:project_id>/<int:invoice_id>/', views.send_invoice_email, name='send_invoice_email'),
    path('cancel_proposal/<int:proposal_id>/', views.cancel_proposal, name='cancel_proposal'),
    path('cancel_project/<int:project_id>/', views.cancel_project, name='cancel_project'),
]


if django_settings.DEBUG is False:
    urlpatterns += static(django_settings.STATIC_URL, document_root=django_settings.STATIC_ROOT)
