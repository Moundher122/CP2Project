# Generated by Django 4.2.19 on 2025-02-25 14:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('application', '0001_initial'),
        ('Auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('leader', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='owned_teams', to=settings.AUTH_USER_MODEL)),
                ('students', models.ManyToManyField(related_name='teams', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Opportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('Type', models.CharField(choices=[('internship', 'Internship'), ('Problem', 'Problem')], max_length=20)),
                ('category', models.CharField(choices=[('EC', 'Economics'), ('CS', 'Computer Science & IT'), ('EN', 'Engineering'), ('HL', 'Healthcare'), ('BM', 'Business & Management'), ('LW', 'Law'), ('ED', 'Education'), ('AH', 'Arts & Humanities')], max_length=30)),
                ('status', models.CharField(choices=[('open', 'Open'), ('closed', 'Closed')], default='open', max_length=15)),
                ('endday', models.DateField(null=True)),
                ('applications', models.ManyToManyField(related_name='opportunities', to='application.application')),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opportunity', to=settings.AUTH_USER_MODEL)),
                ('skills', models.ManyToManyField(to='Auth.skills', verbose_name='Skills')),
            ],
        ),
    ]
