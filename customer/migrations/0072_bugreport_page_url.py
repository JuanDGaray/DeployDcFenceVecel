from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0071_bug_reports'),
    ]

    operations = [
        migrations.AddField(
            model_name='bugreport',
            name='page_url',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
