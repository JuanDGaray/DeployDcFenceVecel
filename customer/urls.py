from django import utils
from django.urls import path
from . import views

urlpatterns = [
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
    ]
