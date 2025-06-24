from django.urls import path
from . import views 

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Financial Report
    path('financial-report/', views.financial_report, name='financial-report'),

    # Accounts
    path('accounts/', views.account_list_view, name='account-list'),
    path('accounts/add_account/', views.add_account, name='add-account'),
    path('accounts/delete_account/', views.delete_account, name='delete-account'),

    # Transactions
    path('add_payment_received/', views.add_payment_received, name='add-payment-received'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/<int:pk>/update/', views.TransactionUpdateView.as_view(), name='transaction-update'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction-delete'),

    # Expenses
    path('expenses/', views.ExpenseListView.as_view(), name='expense-list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense-create'),
    path('expenses/<int:pk>/update/', views.ExpenseUpdateView.as_view(), name='expense-update'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense-delete'),

    # Reports
    path('reports/', views.ReportListView.as_view(), name='report-list'),
    path('reports/create/', views.ReportCreateView.as_view(), name='report-create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('reports/<int:pk>/delete/', views.ReportDeleteView.as_view(), name='report-delete'),

    #gets
    path('get_accounts_payment/', views.get_accounts_payment, name='get_accounts_payment'),
] 