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
from django.urls import path
from customer import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.closeSession, name='logout'),
    path('customers/', views.customers, name='customers'),
    path('projects/', views.projects, name='projects'),
    path('production/', views.production, name='production'),
    path('production/<int:project_id>', views.production_project, name='production_project'),
    path('projects/<int:project_id>/', views.detail_project, name='detail_project'),
    path('projects/<int:project_id>/new_budget/', views.new_budget, name='new_budget'),
    path('projects/<int:project_id>/view_budget/<int:budget_id>', views.view_budget, name='view_budget'),
    path('projects/<int:project_id>/edit_budget/<int:budget_id>', views.edit_budget, name='edit_budget'),
    path('projects/<int:project_id>/delete_budget/<int:budget_id>', views.delete_budget, name='delete_budget'),
    path('projects/<int:project_id>/delete_invoice/<int:invoice_id>', views.delete_invoice, name='delete_invoice'),
    path('projects/<int:project_id>/view_budgetSimple/<int:budget_id>', views.view_budgetSimple, name='view_budgetSimple'),
    path('project/<int:project_id>/view_budget/<int:budget_id>/budgetPrint', views.generate_pdf, name='budget_pdf'),
    path('customers/<int:client_id>/', views.detail_customer, name='detail_customer'),
    path('customers/edit/<int:client_id>/', views.edit_customer, name='edit_customer'),
    path('customers/<int:client_id>/delete/', views.delete_customer, name='delete_customer'),
    path('search_customers/', views.search_customers, name='search_customers'),
    path('search_projects/', views.search_projects, name='search_projects'),
    path('check-email/', views.check_email_exists, name='check_email'),
    
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
