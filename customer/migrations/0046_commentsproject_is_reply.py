# Generated by Django 5.1.1 on 2025-06-24 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0045_commentsproject_mentioned_users_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentsproject',
            name='is_reply',
            field=models.BooleanField(default=False),
        ),
    ]
