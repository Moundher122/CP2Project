# Generated by Django 5.0.6 on 2025-02-16 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opportunity',
            name='daysleft',
        ),
        migrations.AddField(
            model_name='opportunity',
            name='endday',
            field=models.DateField(null=True),
        ),
    ]
