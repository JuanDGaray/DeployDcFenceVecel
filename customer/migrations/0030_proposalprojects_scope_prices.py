# Generated by Django 5.1.1 on 2025-04-10 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0029_proposalprojects_exclusions'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposalprojects',
            name='scope_prices',
            field=models.JSONField(blank=True, default=dict, verbose_name='Scope Prices'),
        ),
    ]
