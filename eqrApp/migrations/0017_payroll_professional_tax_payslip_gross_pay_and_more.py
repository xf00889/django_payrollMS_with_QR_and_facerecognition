# Generated by Django 4.0.3 on 2024-06-02 17:58

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eqrApp', '0016_remove_employee_user_remove_payroll_professional_tax_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='payroll',
            name='professional_tax',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='payslip',
            name='gross_pay',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AlterField(
            model_name='payslip',
            name='professional_tax',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
