# Generated by Django 5.0.6 on 2025-02-02 22:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Auth', '0008_alter_mcf_user'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': [('company', 'company'), ('student', 'student')]},
        ),
    ]
