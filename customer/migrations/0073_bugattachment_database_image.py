from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0072_bugreport_page_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='bugattachment',
            name='data',
            field=models.BinaryField(null=True),
        ),
        migrations.AddField(
            model_name='bugattachment',
            name='content_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='bugattachment',
            name='original_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='bugattachment',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='bug_reports/%Y/%m/'),
        ),
    ]
