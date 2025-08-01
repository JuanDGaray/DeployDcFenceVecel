from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.validators import EmailValidator, ValidationError
from django.contrib.auth.password_validation import validate_password
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import traceback
from ..models import CostItemDescription

@login_required
def settings(request):
    groups = Group.objects.prefetch_related("user_set").all()

    admin_users = []
    sales_users = []
    production_users = []
    for group in groups:
        if group.name == "ADMIN":
            admin_users = [{"name": user.first_name + user.last_name, "email": user.email, "user": user} for user in group.user_set.all()]
        elif group.name == "SALES":
            sales_users = [{"name": user.first_name + user.last_name, "email": user.email, "user": user} for user in group.user_set.all()]
        elif group.name == "PRODUCTION":
            production_users = [{"name": user.first_name + user.last_name, "email": user.email, "user": user} for user in group.user_set.all()]

    return render(request, "settings.html", {
        "admin_users": admin_users,
        "sales_users": sales_users,
        "production_users": production_users,
    })


@login_required
def add_user_post(request):
    if request.method == "POST":
        try:
            # Obtener los datos del formulario
            first_name = request.POST.get("firstName")
            last_name = request.POST.get("lastName")
            email = request.POST.get("email")
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirmPassword")
            group = request.POST.get("group")
            username = email
            print(first_name, last_name, email, password, confirm_password, group)

            # Validar contraseñas coincidentes
            if password != confirm_password:
                return JsonResponse({"statusText": "Passwords do not match"}, status=400)

            # Validar formato del email
            try: 
                EmailValidator()(email)
            except ValidationError:
                print("invalid email")
                return JsonResponse({"statusText": "Invalid email"}, status=400)

            # Validar que el email no exista
            if User.objects.filter(email=email).exists():
                print("email already exists")
                return JsonResponse({"error": "Email already exists"}, status=400)

            # Validar permisos de usuario
            if not request.user.groups.filter(name="ADMIN").exists() and not request.user.is_superuser:
                return JsonResponse({"error": "You are not authorized to add users"}, status=403)

            # Validar grupo existente
            try:
                group_obj = Group.objects.get(name=group)
            except Group.DoesNotExist:
                return JsonResponse({"error": "Group does not exist"}, status=400)

            # Validar robustez de la contraseña
            try:
                validate_password(password)
            except ValidationError as e:
                return JsonResponse({"error": list(e)}, status=400)

            # Crear usuario
            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                username=username
            )
            user.groups.add(group_obj)
            user.save()

            return JsonResponse({"success": "User created successfully"}, status=200)

        except Exception as e:
            # Imprimir stack trace para identificar errores
            print(traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def delete_user(request):
    if request.method == "POST":
        if not request.user.is_superuser:
            return JsonResponse({"error": "You are not authorized to delete users"}, status=403)
        if request.user.id == request.POST.get("user_id"):
            return JsonResponse({"error": "You cannot delete yourself, request a Juan Garay to delete you"}, status=403)
        try:
            user_id = request.POST.get("user_id")
            print('user_id', user_id)
            user = User.objects.get(id=user_id)
            user.delete()
            return JsonResponse({"success": "User deleted successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def edit_cost_item_descriptions(request):
    try:
        # Parse JSON data
        data = json.loads(request.body)
        category = data.get('category')
        original_description = data.get('original_description')
        custom_description = data.get('custom_description')
        
        # Validate required fields
        if not all([category, original_description, custom_description]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Validate category
        valid_categories = ['materials', 'labor', 'contractors', 'utilities', 'overhead', 'miscellaneous', 'deducts', 'profit']
        if category not in valid_categories:
            return JsonResponse({
                'success': False,
                'error': 'Invalid category'
            }, status=400)
        
        # Save or update the custom description
        cost_item_desc, created = CostItemDescription.objects.update_or_create(
            category=category,
            original_description=original_description,
            defaults={
                'custom_description': custom_description,
                'updated_by': request.user
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Description updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error in edit_cost_item_descriptions: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)