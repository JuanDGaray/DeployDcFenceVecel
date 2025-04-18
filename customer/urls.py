from django.urls import path
from . import views

urlpatterns = [
    path('get_proposals/<int:page>/', views.get_proposals, name='get_proposals'),
]