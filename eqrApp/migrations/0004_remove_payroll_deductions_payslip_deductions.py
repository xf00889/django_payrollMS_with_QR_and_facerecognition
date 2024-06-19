# Generated by Django 4.0.3 on 2024-06-01 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eqrApp', '0003_payroll_deductions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payroll',
            name='deductions',
        ),
        migrations.AddField(
            model_name='payslip',
            name='deductions',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
