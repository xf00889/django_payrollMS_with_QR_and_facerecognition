from decimal import Decimal

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from . import models
from .models import Payroll, Employee


class SaveEmployee(forms.ModelForm):
    employee_code = forms.CharField(max_length=250, label="Company ID")
    first_name = forms.CharField(max_length=250, label="First Name")
    middle_name = forms.CharField(max_length=250, label="Middle Name", required=False)
    last_name = forms.CharField(max_length=250, label="Last Name")
    dob = forms.DateField(label="Birthday")
    gender = forms.ChoiceField(choices=[("Male", "Male"), ("Female", "Female")], label="Gender")
    contact = forms.CharField(max_length=250, label="Contact #")
    email = forms.CharField(max_length=250, label="Email")
    address = forms.CharField(widget=forms.Textarea, label="Address")
    department = forms.CharField(max_length=250, label="Department")
    position = forms.CharField(max_length=250, label="Position")
    avatar = forms.ImageField(label="Avatar", required=False)

    class Meta:
        model = Employee
        fields = (
            'employee_code', 'first_name', 'middle_name', 'last_name', 'dob', 'gender', 'contact', 'email', 'address',
            'department', 'position', 'avatar')

    def clean_employee_code(self):
        employee_code = self.cleaned_data['employee_code']
        id = self.data.get('id')
        if id:
            if Employee.objects.exclude(id=id).filter(employee_code=employee_code).exists():
                raise ValidationError(f"Employee code {employee_code} already exists.")
        else:
            if Employee.objects.filter(employee_code=employee_code).exists():
                raise ValidationError(f"Employee code {employee_code} already exists.")
        return employee_code

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar', False)
        if avatar:
            # Check file size (15 MB limit)
            if avatar.size > 15 * 1024 * 1024:
                raise ValidationError("File size exceeds the limit of 15 MB.")
        return avatar

class PayrollForm(forms.ModelForm):
    start_date = forms.DateField(label="Start Date")
    end_date = forms.DateField(label="End Date")

    class Meta:
        model = Payroll
        fields = [
            'start_date',
            'end_date',
            'basic_pay',
            'incentive_pay',
            'house_rent_allowance',
            'meal_allowance',
        ]

class EmployeeCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user