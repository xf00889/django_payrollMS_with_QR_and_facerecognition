from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files import File
from django.db import models, IntegrityError
from django.utils import timezone
import qrcode
from io import BytesIO
from PIL import Image
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    employee_code = models.CharField(max_length=100)
    first_name = models.CharField(max_length=250)
    middle_name = models.CharField(max_length=250, null=True, blank=True)
    last_name = models.CharField(max_length=250)
    gender = models.CharField(max_length=50, choices=(("Male", "Male"), ("Female", "Female")), default="Male")
    dob = models.DateField(null=True, blank=True)
    contact = models.CharField(max_length=100)
    email = models.CharField(max_length=250, blank=True, null=True)
    address = models.TextField(null=True, blank=True)
    department = models.TextField(null=True, blank=True)
    position = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to="employee-avatars/", null=True, blank=True)
    qr_code = models.ImageField(upload_to="qr_codes/", null=True, blank=True)
    date_added = models.DateTimeField(default=timezone.now)
    date_created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_code} - {self.first_name} {self.middle_name if self.middle_name else ''} {self.last_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code:
            self.generate_qr_code()

    def generate_qr_code(self):
        qr_image = qrcode.make(self.employee_code)
        qr_offset = Image.new('RGB', (310, 310), 'white')
        qr_offset.paste(qr_image)
        stream = BytesIO()
        qr_offset.save(stream, 'PNG')
        self.qr_code.save(f'{self.employee_code}.png', File(stream), save=False)


class FacialData(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='facial_data')
    image = models.ImageField(upload_to="facial-data/")
    date_recorded = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Facial Data for {self.employee.employee_code} recorded on {self.date_recorded}"


class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2)
    incentive_pay = models.DecimalField(max_digits=10, decimal_places=2)
    house_rent_allowance = models.DecimalField(max_digits=10, decimal_places=2)
    meal_allowance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payroll for {self.employee} - {self.start_date} to {self.end_date}"


class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    date_received = models.DateTimeField(default=timezone.now)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payslip for {self.employee} - {self.payroll.start_date} to {self.payroll.end_date}"

    def save(self, *args, **kwargs):
        try:

            if self.employee.attendance_set.filter(
                    date__range=[self.payroll.start_date, self.payroll.end_date],
                    present=True).exists():

                total_hours_within_pay_period = self.employee.attendance_set.filter(
                    date__range=[self.payroll.start_date, self.payroll.end_date],
                    present=True).count() * 8

                hourly_rate = self.payroll.basic_pay / Decimal(8)

                if total_hours_within_pay_period > 8 * (self.payroll.end_date - self.payroll.start_date).days:
                    regular_hours = 8 * (self.payroll.end_date - self.payroll.start_date).days
                    overtime_hours = total_hours_within_pay_period - regular_hours
                    regular_pay = hourly_rate * Decimal(regular_hours)
                    overtime_pay = hourly_rate * Decimal('1.5') * Decimal(overtime_hours)
                    self.gross_pay = regular_pay + overtime_pay + self.payroll.incentive_pay + self.payroll.meal_allowance + self.payroll.house_rent_allowance
                else:
                    self.gross_pay = hourly_rate * Decimal(
                        total_hours_within_pay_period) + self.payroll.incentive_pay + self.payroll.meal_allowance + self.payroll.house_rent_allowance


                self.professional_tax = self.calculate_tax(self.gross_pay)


                self.net_pay = self.gross_pay - self.professional_tax

                super().save(*args, **kwargs)
            else:

                pass

        except IntegrityError as e:
            logger.error(f"IntegrityError for {self.employee}: {e}")

    def calculate_tax(self, gross_pay):

        tax_brackets = {
            0: (Decimal('10416.67'), Decimal('10416.67')),
            1: (Decimal('10416.68'), Decimal('16666.67')),
            2: (Decimal('16666.68'), Decimal('33333.33')),
            3: (Decimal('33333.34'), Decimal('83333.33')),
            4: (Decimal('83333.34'), Decimal('333333.33')),
            5: (Decimal('333333.34'), Decimal('9999999999'))
        }

        current_tax_bracket = 0
        total_tax = Decimal('0.00')
        for index, bounds in tax_brackets.items():
            lower_bound, upper_bound = bounds
            if lower_bound <= gross_pay <= upper_bound:
                current_tax_bracket = index
                break

        tax_rates = {
            0: Decimal('0.00'),
            1: Decimal('0.15'),
            2: Decimal('0.20'),
            3: Decimal('0.25'),
            4: Decimal('0.30'),
            5: Decimal('0.35')
        }

        for i in range(current_tax_bracket + 1):
            lower_bound, upper_bound = tax_brackets[i]
            tax_rate = tax_rates[i]
            tax = (upper_bound - lower_bound) * tax_rate
            total_tax += tax

        return total_tax

# class Payslip(models.Model):
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
#     net_pay = models.DecimalField(max_digits=10, decimal_places=2)
#     date_received = models.DateTimeField(default=timezone.now)
#     professional_tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     gross_pay = models.DecimalField(max_digits=10, decimal_places=2)
#
#     def __str__(self):
#         return f"Payslip for {self.employee} - {self.payroll.start_date} to {self.payroll.end_date}"
#
#     def save(self, *args, **kwargs):
#         try:
#             total_hours_within_pay_period = self.employee.attendance_set.filter(
#                 date__range=[self.payroll.start_date, self.payroll.end_date],
#                 present=True).count() * 8
#
#             hourly_rate = self.payroll.basic_pay / Decimal(8)
#
#             if total_hours_within_pay_period > 8 * (self.payroll.end_date - self.payroll.start_date).days:
#                 regular_hours = 8 * (self.payroll.end_date - self.payroll.start_date).days
#                 overtime_hours = total_hours_within_pay_period - regular_hours
#                 regular_pay = hourly_rate * Decimal(regular_hours)
#                 overtime_pay = hourly_rate * Decimal('1.5') * Decimal(overtime_hours)
#                 self.gross_pay = regular_pay + overtime_pay + self.payroll.incentive_pay + self.payroll.meal_allowance + self.payroll.house_rent_allowance
#             else:
#                 self.gross_pay = hourly_rate * Decimal(total_hours_within_pay_period) + self.payroll.incentive_pay + self.payroll.meal_allowance + self.payroll.house_rent_allowance
#
# if self.payroll.start_date.day == 15:
#     tax_thresholds = {
#         0: Decimal('10416.67'),
#         1: (Decimal('10416.68'), Decimal('16666.67')),
#         2: (Decimal('16666.68'), Decimal('33333.33')),
#         3: (Decimal('33333.34'), Decimal('83333.33')),
#         4: (Decimal('83333.34'), Decimal('333333.33')),
#         5: Decimal('333333.34')
#     }
# else:
#     tax_thresholds = {
#         0: Decimal('20833.33'),
#         1: (Decimal('20833.34'), Decimal('33333.33')),
#         2: (Decimal('33333.34'), Decimal('66666.67')),
#         3: (Decimal('66666.68'), Decimal('166666.67')),
#         4: (Decimal('166666.68'), Decimal('666666.67')),
#         5: Decimal('666666.68')
#     }

#             current_tax_bracket = 0
#             for index, bounds in tax_thresholds.items():
#                 if isinstance(bounds, Decimal):
#                     if self.gross_pay <= bounds:
#                         current_tax_bracket = index
#                         break
#                 else:
#                     lower_bound, upper_bound = bounds
#                     if lower_bound <= self.gross_pay <= upper_bound:
#                         current_tax_bracket = index
#                         break
#
#             lower_bound = tax_thresholds[current_tax_bracket][0] if isinstance(tax_thresholds[current_tax_bracket], tuple) else Decimal('0.00')
#             tax_rates = {
#                 0: Decimal('0.00'),
#                 1: Decimal('0.15'),
#                 2: Decimal('0.20'),
#                 3: Decimal('0.25'),
#                 4: Decimal('0.30'),
#                 5: Decimal('0.35')
#             }
#             tax_rate = tax_rates[current_tax_bracket]
#
#             if current_tax_bracket == 0:
#                 self.professional_tax = Decimal('0.00')
#             else:
#                 self.professional_tax = (self.gross_pay - lower_bound) * tax_rate
#
#
#             self.net_pay = self.gross_pay - self.professional_tax
#
#             super().save(*args, **kwargs)
#
#         except IntegrityError as e:
#             logger.error(f"IntegrityError for {self.employee}: {e}")
#

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('I', 'In'),
        ('O', 'Out'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=True)
    morning_check_in = models.DateTimeField(null=True, blank=True)
    morning_check_out = models.DateTimeField(null=True, blank=True)
    afternoon_check_in = models.DateTimeField(null=True, blank=True)
    afternoon_check_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"{self.employee.first_name} "
            f"{self.employee.middle_name if self.middle_name else ''} "
            f"{self.employee.last_name} - {self.date}"
        )
