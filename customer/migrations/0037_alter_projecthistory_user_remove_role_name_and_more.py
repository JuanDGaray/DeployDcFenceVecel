# Generated by Django 5.1.1 on 2025-06-22 19:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0036_paymentsreceived'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='projecthistory',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Usuario'),
        ),
        migrations.RemoveField(
            model_name='role',
            name='name',
        ),
        migrations.AddField(
            model_name='role',
            name='users',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='role', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='role',
            name='hierarchy_level',
            field=models.CharField(choices=[('1', 'Admin'), ('2', 'Sales'), ('2', 'Production')], default='1', max_length=20),
        ),
        migrations.AlterField(
            model_name='role',
            name='role_type',
            field=models.CharField(choices=[('admin', 'Administrador'), ('sales', 'Vendedor'), ('production', 'Producción')], default='admin', max_length=20),
        ),
        migrations.DeleteModel(
            name='User',
        ),
    ]
