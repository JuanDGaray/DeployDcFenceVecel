# Generated by Django 5.1.1 on 2025-01-20 13:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0016_taskproject'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskproject',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='taskproject',
            name='name',
        ),
        migrations.RemoveField(
            model_name='taskproject',
            name='progress',
        ),
        migrations.RemoveField(
            model_name='taskproject',
            name='start_date',
        ),
    ]
