from django.contrib import admin
from django.apps import apps

# Obtiene todos los modelos de la aplicación
app = apps.get_app_config('customer')

# Registra todos los modelos en el admin
for model in app.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass