# Generated by Django 5.1.1 on 2024-12-18 05:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='folder_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Folder ID'),
        ),
    ]
