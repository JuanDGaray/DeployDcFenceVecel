from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_analytics, name='index_analytics'), # Dashboard
    path('<str:report_type>/<int:user_id>/', views.analytics_dashboard, name='analytics_dashboard'), # Dashboard
    path('send/gmail_metrics/<int:user_id>/', views.send_gmail_metrics, name='send_gmail_metrics'), # Dashboard
    path('update_base64/', views.update_base64, name='update_base64'), # Dashboard
    path('daily_analysis/', views.daily_analysis, name='daily_analysis'), # Dashboard
    path('send/gmail_daily/<int:user_id>/', views.send_gmail_daily, name='send_gmail_daily'), # Dashboard
]