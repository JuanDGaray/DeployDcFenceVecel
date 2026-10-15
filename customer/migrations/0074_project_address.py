from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0073_bugattachment_database_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='address',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Address'),
        ),
    ]
