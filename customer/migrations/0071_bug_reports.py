import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0070_changeorderdetail_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BugReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('urgency', models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='medium', max_length=20)),
                ('status', models.CharField(choices=[('new', 'New'), ('pending', 'Pending'), ('in_progress', 'In progress'), ('in_review', 'In review'), ('resolved', 'Resolved'), ('closed', 'Closed'), ('reopened', 'Reopened')], default='new', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assignee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_bugs', to=settings.AUTH_USER_MODEL)),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reported_bugs', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='BugAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='bug_reports/%Y/%m/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='customer.bugreport')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bug_attachments', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.CreateModel(
            name='BugComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bug_comments', to=settings.AUTH_USER_MODEL)),
                ('bug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='customer.bugreport')),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.CreateModel(
            name='BugChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('is_done', models.BooleanField(default=False)),
                ('position', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_items', to='customer.bugreport')),
            ],
            options={'ordering': ['position', 'id']},
        ),
        migrations.CreateModel(
            name='BugHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=40)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='customer.bugreport')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bug_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('mention', 'Mention'), ('reply', 'Reply'), ('project_update', 'Project Update'), ('status_change', 'Status Change'), ('manager_assignment', 'Manager Assignment'), ('bug_report', 'Bug Report'), ('bug_assigned', 'Bug Assigned'), ('bug_status', 'Bug Status'), ('bug_comment', 'Bug Comment')], max_length=20),
        ),
        migrations.AlterField(
            model_name='notification',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='customer.project'),
        ),
        migrations.AddField(
            model_name='notification',
            name='bug',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='customer.bugreport'),
        ),
    ]
