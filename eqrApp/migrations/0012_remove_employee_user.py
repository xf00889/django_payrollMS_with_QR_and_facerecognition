# Generated by Django 4.0.3 on 2024-06-02 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eqrApp', '0011_employee_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='user',
        ),
    ]
