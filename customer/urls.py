from django.urls import path
from . import views

urlpatterns = [
    path('get_proposals/<int:page>/', views.get_proposals, name='get_proposals'),
    path('get_userInfo/<int:id_user>/', views.get_userInfo, name='get_userInfo'),
    path('get_user_info/', views.get_userInfo, name='get_user_info'),
    path('get_projects/<int:page>/', views.get_projects, name='get_projects'),
    path('duplicate_project/<int:project_id>/<int:customer_id>/', views.duplicate_project, name='duplicate_project'),
]