from django.shortcuts import render
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def my_space(request):
    sales_advisors = User.objects.filter()
    user_id = request.user.id
    return render(request, 'my_space.html', {'sales_advisors': sales_advisors, 'user_id': user_id})

