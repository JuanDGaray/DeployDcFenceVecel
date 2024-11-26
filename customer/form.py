from django.forms import ModelForm
from .models import Customer, Project

class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name',
                  'last_name',
                  'company_name',
                  'customer_type',
                  'email',
                  'phone',
                  'address',
                  'city',
                  'state',
                  'zip_code',
                  'country',
                  ]
        
        
class ProjectsForm(ModelForm):
    class Meta:
        model = Project
        fields = ['project_name',
                  'customer',
                  'start_date',
                  'end_date',
                  'status',
                  'description',
                  'estimated_cost',
                  'city',
                  'state',
                  'zip_code',
                  'country',
                ]