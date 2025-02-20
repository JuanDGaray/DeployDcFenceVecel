from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import Group

@login_required
def settings(request):
    groups = Group.objects.prefetch_related("user_set").all()

    admin_users = []
    sales_users = []
    production_users = []
    for group in groups:
        if group.name == "ADMIN":
            admin_users = [{"name": user.first_name + user.last_name, "email": user.email} for user in group.user_set.all()]
        elif group.name == "SALES":
            sales_users = [{"name": user.first_name + user.last_name, "email": user.email} for user in group.user_set.all()]
        elif group.name == "PRODUCTION":
            production_users = [{"name": user.first_name + user.last_name, "email": user.email} for user in group.user_set.all()]

    return render(request, "settings.html", {
        "admin_users": admin_users,
        "sales_users": sales_users,
        "production_users": production_users,
    })

