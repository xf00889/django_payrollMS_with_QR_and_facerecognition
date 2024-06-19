# Generated by Django 4.0.3 on 2024-06-02 11:20

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eqrApp', '0009_alter_payroll_professional_tax'),
    ]

    operations = [
        migrations.AddField(
            model_name='payslip',
            name='gross_pay',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
