from __future__ import print_function

import logging
import os

import face_recognition
import sib_api_v3_sdk
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.utils.baseconv import base64
from sib_api_v3_sdk.rest import ApiException
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from .forms import PayrollForm, SaveEmployee, EmployeeCreationForm
from .models import Payroll, Employee, Attendance, Payslip, FacialData
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
import base64
from .models import Employee, FacialData


def context_data():
    return {
        'page_name': '',
        'page_title': 'Chat Room',
        'system_name': 'QR-APMS Mighty Hok',
        'topbar': True,
        'footer': True,
    }


# View to handle the login page
def login_page(request):
    context = context_data()
    context.update({'topbar': False, 'footer': False, 'page_name': 'login', 'page_title': 'Login'})
    return render(request, 'login.html', context)


# View to handle user login
from django.http import JsonResponse


def login_user(request):
    logout(request)
    resp = {"status": 'failed', 'msg': ''}
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status'] = 'success'
                if user.is_superuser:
                    return JsonResponse({'status': 'success', 'redirect_url': '/admin_page/'})  # Redirect to admin page
                else:
                    return JsonResponse(
                        {'status': 'success', 'redirect_url': '/attendance_emp/'})  # Redirect to employee page
            else:
                resp['msg'] = "Inactive account"
        else:
            resp['msg'] = "Incorrect username or password"
    return JsonResponse(resp)


@login_required
def employee_page(request):
    # Your logic for the employee page
    context = context_data()
    context.update({'page_name': 'employee', 'page_title': 'Employee Dashboard'})
    return render(request, 'employee.html', context)


@login_required
def create_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            print("New user created:", new_user.username)
            print("Password:", form.cleaned_data['password'])  # Make sure the password is correct
            return redirect('create-employee')
    else:
        form = EmployeeCreationForm()
    return render(request, 'create_employee.html', {'form': form})


@login_required
def home(request):
    present_employees_count = Attendance.objects.filter(date=timezone.now(), present=True).values('employee').annotate(
        count=Count('employee')).count()

    # Prepare the context data
    context = context_data()
    context.update({
        'page': 'home',
        'page_title': 'Home',
        'employees': Employee.objects.count(),
        'present_employees': present_employees_count
    })

    return render(request, 'home.html', context)


def logout_user(request):
    logout(request)
    return redirect('login-page')


@login_required
def employee_list(request):
    context = context_data()
    employees = Employee.objects.all()
    context.update({
        'page': 'employee_list',
        'page_title': 'Employee List',
        'employees': employees,
    })

    sample_employee = employees.first()
    if sample_employee:
        context['employee'] = sample_employee
    else:
        context['employee'] = None

    return render(request, 'employee_list.html', context)


# View to manage (add/edit) employees


# @csrf_exempt
# @require_http_methods(["POST"])
# def save_employee(request):
#     resp = {'status': 'failed', 'msg': ''}
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         email = request.POST.get('email')  # Retrieve email from POST data
#
#         # Check if the user already exists
#         if User.objects.filter(username=username).exists():
#             resp['msg'] = 'User already exists. Please choose a different username.'
#         else:
#             try:
#                 with transaction.atomic():
#                     user = User.objects.create_user(username=username, password=password, email=email)  # Include email in user creation
#                     user.is_staff = True  # Set is_staff permission to True
#                     user.save()
#
#                     employee_id = request.POST.get('id', '')
#                     employee_instance = get_object_or_404(Employee, id=employee_id) if employee_id else None
#                     employee_form = SaveEmployee(request.POST, request.FILES, instance=employee_instance)
#
#                     if employee_form.is_valid():
#                         employee = employee_form.save()
#                         messages.success(request,
#                                          f"{employee.employee_code} has been {'updated' if employee_id else 'added'} successfully.")
#                         resp['status'] = 'success'
#                     else:
#                         error_messages = [f"[{field.label}] {error}" for field in employee_form for error in
#                                           field.errors]
#                         resp['msg'] = "<br />".join(error_messages)
#             except Exception as e:
#                 logger.error("An error occurred while saving the employee data: %s", e)
#                 resp['msg'] = "An error occurred while saving the data. Please try again."
#     else:
#         resp['msg'] = "No data has been sent into the request."
#
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         return JsonResponse(resp)
#     else:
#         if resp['status'] == 'success':
#             return redirect('employee-list')
#         else:
#             messages.error(request, resp['msg'])
#             return redirect('add-employee')


logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def save_employee(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        employee_id = request.POST.get('id', '')
        employee_instance = get_object_or_404(Employee, id=employee_id) if employee_id else None

        if employee_instance:
            employee_form = SaveEmployee(request.POST, request.FILES, instance=employee_instance)
            if employee_form.is_valid():
                try:
                    with transaction.atomic():
                        employee = employee_form.save()
                        messages.success(request, f"{employee.employee_code} has been updated successfully.")
                        resp['status'] = 'success'
                except Exception as e:
                    logger.error("An error occurred while updating the employee data: %s", e)
                    resp['msg'] = "An error occurred while updating the data. Please try again."
            else:
                resp['msg'] = "<br />".join(
                    [f"[{field.label}] {error}" for field in employee_form for error in field.errors])
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')

            if not username or not password or not email:
                resp['msg'] = 'All fields are required: username, password, and email.'
            elif User.objects.filter(username=username).exists():
                resp['msg'] = 'User already exists. Please choose a different username.'
            else:
                try:
                    with transaction.atomic():
                        user = User.objects.create_user(username=username, password=password, email=email)
                        user.is_staff = True
                        user.save()

                        configuration = sib_api_v3_sdk.Configuration()
                        configuration.api_key[
                            'api-key'] = ''
                        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

                        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                            to=[{"email": email, "name": username}],
                            sender={"name": "Mighty Hok Summit", "email": "hutchiejn@gmail.com"},
                            subject="Employee Account Details",
                            html_content=f"<html><head></head><body><p>Hello {username},</p><p>Your account has been created successfully. Your username is {username} and your password is {password}.</p></body></html>"
                        )

                        try:
                            api_response = api_instance.send_transac_email(send_smtp_email)
                            print(api_response)
                        except ApiException as e:
                            print(f"Exception when calling SMTPApi->send_transac_email: {e}")

                        employee_form = SaveEmployee(request.POST, request.FILES)
                        if employee_form.is_valid():
                            employee = employee_form.save()
                            messages.success(request, f"{employee.employee_code} has been added successfully.")
                            resp['status'] = 'success'
                        else:
                            resp['msg'] = "<br />".join(
                                [f"[{field.label}] {error}" for field in employee_form for error in field.errors])
                except Exception as e:
                    logger.error("An error occurred while saving the employee data: %s", e)
                    resp['msg'] = "An error occurred while saving the data. Please try again."

        if resp['status'] == 'success':
            return redirect('record-facial-data', employee_id=employee.id)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(resp)
    else:
        if resp['status'] == 'success':
            return redirect('employee-list')
        else:
            messages.error(request, resp['msg'])
            return redirect('add-employee')


def record_facial_data(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'record_facial_data.html', {'employee': employee})

@csrf_exempt
def save_facial_data(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        facial_data = request.POST.get('facial_data')

        if employee_id and facial_data:
            employee = get_object_or_404(Employee, id=employee_id)
            format, imgstr = facial_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"{employee.employee_code}_facial_data.{ext}")

            facial_data_record = FacialData(employee=employee)
            facial_data_record.image.save(data.name, data, save=True)

            return JsonResponse({'status': 'success', 'msg': 'Facial data saved successfully'})
        else:
            return JsonResponse({'status': 'failed', 'msg': 'Invalid data provided'})
    return JsonResponse({'status': 'failed', 'msg': 'Invalid request method'})




#backup
# @csrf_exempt
# @require_http_methods(["POST"])
# def save_employee(request):
#     resp = {'status': 'failed', 'msg': ''}
#     if request.method == 'POST':
#         employee_id = request.POST.get('id', '')
#         employee_instance = get_object_or_404(Employee, id=employee_id) if employee_id else None
#         employee_form = SaveEmployee(request.POST, request.FILES, instance=employee_instance)
#
#         if employee_form.is_valid():
#             try:
#                 with transaction.atomic():
#                     employee = employee_form.save()
#                     messages.success(request,
#                                      f"{employee.employee_code} has been {'updated' if employee_id else 'added'} successfully.")
#                     resp['status'] = 'success'
#             except Exception as e:
#                 logger.error("An error occurred while saving the employee data: %s", e)
#                 resp['msg'] = "An error occurred while saving the data. Please try again."
#         else:
#             error_messages = [f"[{field.label}] {error}" for field in employee_form for error in field.errors]
#             logger.error("Employee form errors: %s", error_messages)
#             resp['msg'] = "<br />".join(error_messages)
#     else:
#         resp['msg'] = "No data has been sent into the request."
#
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         return JsonResponse(resp)
#     else:
#         if resp['status'] == 'success':
#             return redirect('employee-list')
#         else:
#             messages.error(request, resp['msg'])
#             return redirect('add-employee')
@login_required
def manage_employee(request, pk=None, add_payroll=None):
    context = context_data()

    if pk is None:
        context.update({'page': 'add_employee', 'page_title': 'Add New Employee', 'employee': {}})
    elif add_payroll:
        employee = get_object_or_404(Employee, id=pk)
        payroll = Payroll.objects.filter(employee=employee).first()
        context.update(
            {'page': 'add_payroll', 'page_title': 'Add Payroll', 'employee': employee, 'payroll': payroll}
        )
        return render(request, 'add_pay_info.html', context)  # Render the new template for adding payroll information
    else:
        employee = get_object_or_404(Employee, id=pk)
        payroll = Payroll.objects.filter(employee=employee).first()

        context.update(
            {'page': 'edit_employee', 'page_title': 'Update Employee', 'employee': employee, 'payroll': payroll}
        )

    return render(request, 'manage_employee.html', context)


def create_user(request, employee_id=None):
    if request.method == 'GET':
        employees = Employee.objects.all()
        return render(request, 'create_user.html', {'employees': employees})

    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        employee_code = request.POST.get('employee_code')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {'success': False, 'message': 'User already exists. Please choose a different username.'})

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.is_staff = True
            user.save()

            employee = Employee.objects.create(user=user, employee_code=employee_code, first_name=first_name,
                                               last_name=last_name)
            return JsonResponse({'success': True, 'message': 'User created successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@login_required
def fetch_employee_profile(request):
    if request.method == 'GET':
        employee_id = request.GET.get('employee_id')
        employee = get_object_or_404(Employee, pk=employee_id)
        profile_data = {
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'department': employee.department,
            'position': employee.position,
        }
        return JsonResponse(profile_data)
    else:
        return HttpResponse(status=400)


def get_employees(request):
    employees = Employee.objects.all()
    employee_data = [{'id': employee.id, 'name': f'{employee.first_name} {employee.last_name}'} for employee in
                     employees]
    return JsonResponse({'employees': employee_data})


logger = logging.getLogger(__name__)


@login_required
def manage_payroll(request, employee_pk=None):
    context = context_data()
    if employee_pk is None:
        context.update({'page': 'add_payroll', 'page_title': 'Add Payroll', 'employee': {}})
    else:
        employee = get_object_or_404(Employee, id=employee_pk)
        payroll = Payroll.objects.filter(employee=employee).first()
        context.update(
            {'page': 'edit_payroll', 'page_title': 'Update Payroll', 'employee': employee, 'payroll': payroll}
        )

    return render(request, 'view_payroll_info.html', context)


def edit_payroll(request, employee_pk):
    employee = get_object_or_404(Employee, id=employee_pk)
    payroll = Payroll.objects.filter(employee=employee).first()

    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll information updated successfully.')
            return redirect('payroll_list')  # Redirect to the payroll list page
    else:
        form = PayrollForm(instance=payroll)

    context = {
        'page': 'edit_payroll',
        'page_title': 'Update Payroll',
        'employee': employee,
        'payroll': payroll,
        'form': form,
    }

    return render(request, 'edit_payroll_info.html', context)


def edit_payroll_info(request, employee_pk):
    payroll = get_object_or_404(Payroll, employee_id=employee_pk)

    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()

    else:
        form = PayrollForm(instance=payroll)

    return render(request, 'edit_payroll_info.html', {'form': form, 'payroll': payroll})


@csrf_exempt
@require_http_methods(["POST"])
def save_payroll(request):
    resp = {'status': 'failed', 'msg': ''}

    if request.method == 'POST':
        form_data = request.POST.dict()
        employee_id = form_data.get('employee_id')
        start_date = form_data.get('start_date')
        end_date = form_data.get('end_date')

        try:
            employee = Employee.objects.get(id=employee_id)
            payroll = Payroll.objects.filter(employee=employee).first()

            form_data['start_date'] = start_date
            form_data['end_date'] = end_date

            form = PayrollForm(form_data, instance=payroll) if payroll else PayrollForm(form_data)

            if form.is_valid():
                payroll = form.save(commit=False)
                payroll.employee = employee
                payroll.save()
                resp['status'] = 'success'
                messages.success(request, 'Payroll information saved successfully.')  # Add success message
            else:
                resp['msg'] = "Form data is invalid. Please check the fields: " + str(form.errors)
        except Employee.DoesNotExist:
            resp['msg'] = "Employee matching query does not exist."
        except Exception as e:
            resp['msg'] = f"An error occurred: {e}"
    else:
        resp['msg'] = "Invalid request method. POST method is required."

    return JsonResponse(resp)


# @csrf_exempt
# @require_http_methods(["POST"])
# def save_payroll(request):
#     resp = {'status': 'failed', 'msg': ''}
#
#     if request.method == 'POST':
#         form_data = request.POST.dict()
#         employee_id = form_data.get('employee_id')
#         start_date = form_data.get('start_date')
#         end_date = form_data.get('end_date')
#
#         try:
#             employee = Employee.objects.get(id=employee_id)
#             payroll = Payroll.objects.filter(employee=employee).first()
#
#             form_data['start_date'] = start_date  # Add start_date to form_data
#             form_data['end_date'] = end_date  # Add end_date to form_data
#
#             form = PayrollForm(form_data, instance=payroll) if payroll else PayrollForm(form_data)
#
#             if form.is_valid():
#                 payroll = form.save(commit=False)
#                 payroll.employee = employee
#                 payroll.save()
#                 resp['status'] = 'success'
#             else:
#                 resp['msg'] = "Form data is invalid. Please check the fields: " + str(form.errors)
#         except Employee.DoesNotExist:
#             resp['msg'] = "Employee matching query does not exist."
#         except Exception as e:
#             resp['msg'] = f"An error occurred: {e}"
#     else:
#         resp['msg'] = "Invalid request method. POST method is required."
#
#     return JsonResponse(resp)
#

def view_payroll(request, pk):
    context = context_data()
    context['employee'] = get_object_or_404(Employee, pk=pk)
    return render(request, "payroll.html", context)


@login_required
def view_card(request, pk):
    context = context_data()
    context['employee'] = get_object_or_404(Employee, id=pk)
    return render(request, 'view_id.html', context)


# View to display the QR scanner page
@login_required
def view_scanner(request):
    context = context_data()
    return render(request, 'scanner.html', context)


# View to display an employee's details
@login_required
def view_details(request, code):
    context = context_data()
    context['employee'] = get_object_or_404(Employee, employee_code=code)
    return render(request, 'view_details.html', context)


# View to delete an employee
@login_required
def delete_employee(request, pk):
    resp = {'status': 'failed', 'msg': ''}
    if pk:
        try:
            Employee.objects.get(id=pk).delete()
            resp['status'] = 'success'
            messages.success(request, 'Employee has been deleted successfully.')
        except:
            resp['msg'] = "Employee has failed to delete."
    else:
        resp['msg'] = "No data has been sent into the request."
    return HttpResponse(json.dumps(resp), content_type="application/json")


logger = logging.getLogger(__name__)


@login_required
def calculate_payroll(request):
    if request.method == 'POST':
        employees = Employee.objects.all()
        logger.info(f"Found {employees.count()} employees.")

        current_date = timezone.now().date()
        current_day = current_date.day

        if current_day not in [15, 30]:
            messages.error(request, "Payroll calculation can only be triggered on the 15th and 30th of the month.")
            return redirect('payroll_list')

        for employee in employees:
            if current_day == 15:
                period_start = current_date.replace(day=1)
                period_end = current_date.replace(day=15)
            elif current_day == 30:  # If the current day is 30, calculate for the end of the month
                period_start = current_date.replace(day=16)
                next_month = current_date.replace(day=1) + timedelta(days=32)  # Go to the next month
                period_end = next_month.replace(day=1) - timedelta(
                    days=1)  # Go back one day to the end of the previous month

            current_payroll = Payroll.objects.filter(
                employee=employee,
                start_date=period_start,
                end_date=period_end
            ).first()

            if current_payroll is None:
                logger.warning(f"No payroll record found for {employee} in the current period.")
                continue

            try:
                total_hours_within_pay_period = employee.attendance_set.filter(
                    date__range=[period_start, period_end],
                    present=True).count() * 8

                hourly_rate = current_payroll.basic_pay / Decimal(8)

                if total_hours_within_pay_period > 8 * (period_end - period_start).days:
                    regular_hours = 8 * (period_end - period_start).days
                    overtime_hours = total_hours_within_pay_period - regular_hours
                    regular_pay = hourly_rate * Decimal(regular_hours)
                    overtime_pay = hourly_rate * Decimal('1.5') * Decimal(overtime_hours)
                    gross_pay = regular_pay + overtime_pay + current_payroll.incentive_pay + current_payroll.meal_allowance + current_payroll.house_rent_allowance
                else:
                    gross_pay = hourly_rate * Decimal(
                        total_hours_within_pay_period) + current_payroll.incentive_pay + current_payroll.meal_allowance + current_payroll.house_rent_allowance

                professional_tax = Decimal('0.00')

                net_pay = gross_pay - professional_tax

                payslip, created = Payslip.objects.get_or_create(
                    employee=employee,
                    payroll=current_payroll,
                    defaults={'date_received': timezone.now(), 'gross_pay': gross_pay,
                              'professional_tax': professional_tax, 'net_pay': net_pay}
                )

                if not created:
                    payslip.date_received = timezone.now()
                    payslip.gross_pay = gross_pay
                    payslip.professional_tax = professional_tax
                    payslip.net_pay = net_pay
                    payslip.save()

                logger.info(f"Payslip generated for {employee}.")

            except IntegrityError as e:
                logger.error(f"IntegrityError for {employee}: {e}")
                messages.error(request, f"Error calculating payroll for {employee}: {e}")
                continue

        messages.success(request, "Payroll calculation completed.")
        return redirect('payroll_list')

    messages.error(request, "Invalid request method.")
    return redirect('payroll_list')


# def calculate_payroll(request):
#     if request.method == 'POST':
#         employees = Employee.objects.all()
#         logger.info(f"Found {employees.count()} employees.")
#
#         current_date = timezone.now().date()
#         current_day = current_date.day
#
#         if current_day not in [15, 30]:
#             messages.error(request, "Payroll calculation can only be triggered on the 15th and 30th of the month.")
#             return redirect('payroll_list')
#
#         if current_day == 15:
#             period_start = current_date.replace(day=1)
#             period_end = current_date.replace(day=15)
#         else:
#             period_start = current_date.replace(day=16)
#             next_month_start = current_date.replace(day=28) + timedelta(days=4)
#             period_end = next_month_start - timedelta(days=next_month_start.day)
#
#         for employee in employees:
#             if employee.payroll_set.filter(end_date__day=15).exists() and current_day == 15:
#                 current_payroll = Payroll.objects.filter(
#                     employee=employee,
#                     start_date=period_start,
#                     end_date=period_end
#                 ).first()
#
#                 if not current_payroll:
#                     logger.warning(f"No payroll record found for {employee} in the current period.")
#                     continue
#
#                 total_hours_within_pay_period = (period_end - period_start).days * 8
#
#                 hours_worked_within_pay_period = employee.attendance_set.filter(
#                     date__range=[period_start, period_end],
#                     present=True
#                 ).count() * 8
#
#                 hourly_rate = current_payroll.basic_pay / Decimal(8)
#
#                 if hours_worked_within_pay_period > 8:
#                     regular_hours = 8
#                     overtime_hours = hours_worked_within_pay_period - 8
#
#                     regular_pay = hourly_rate * Decimal(regular_hours)
#                     overtime_pay = hourly_rate * Decimal('1.5') * Decimal(overtime_hours)
#
#                     gross_pay = regular_pay + overtime_pay + current_payroll.incentive_pay + current_payroll.meal_allowance + current_payroll.house_rent_allowance
#                 else:
#                     gross_pay = hourly_rate * Decimal(hours_worked_within_pay_period) + current_payroll.incentive_pay + current_payroll.meal_allowance + current_payroll.house_rent_allowance
#
#                 # Tax calculation based on the tax brackets
#                 tax_brackets = {
#                     0: Decimal('20833.33'),
#                     1: Decimal('33333.33'),
#                     2: Decimal('66666.67'),
#                     3: Decimal('166666.67'),
#                     4: Decimal('666666.67'),
#                     5: Decimal('666666.68')
#                 }
#
#                 tax_rates = {
#                     0: Decimal('0.15'),
#                     1: Decimal('0.20'),
#                     2: Decimal('0.25'),
#                     3: Decimal('0.30'),
#                     4: Decimal('0.35')
#                 }
#
#                 current_tax_bracket = 0
#                 for index, upper_bound in tax_brackets.items():
#                     if gross_pay <= upper_bound:
#                         current_tax_bracket = index
#                         break
#
#                 current_tax_bracket = max(0, current_tax_bracket)  # Ensure current_tax_bracket is not negative
#
#                 if current_tax_bracket == 0:
#                     lower_bound = Decimal('0')
#                 else:
#                     lower_bound = tax_brackets[current_tax_bracket - 1]
#
#                 tax_rate = tax_rates.get(current_tax_bracket, Decimal('0.35'))
#                 professional_tax = (gross_pay - lower_bound) * tax_rate
#
#                 try:
#                     payslip, created = Payslip.objects.get_or_create(
#                         employee=employee,
#                         payroll=current_payroll,
#                         defaults={
#                             'date_received': timezone.now(),
#                             'gross_pay': gross_pay,
#                             'net_pay': gross_pay - professional_tax,
#                             'professional_tax': professional_tax
#                         }
#                     )
#                     if not created:
#                         payslip.gross_pay = gross_pay
#                         payslip.net_pay = gross_pay - professional_tax
#                         payslip.professional_tax = professional_tax
#                         payslip.date_received = timezone.now()
#                         payslip.save()
#                 except IntegrityError as e:
#                     logger.error(f"IntegrityError for {employee}: {e}")
#                     messages.error(request, f"Error calculating payroll for {employee}: {e}")
#                     continue
#
#         messages.success(request, "Payroll calculation completed.")
#         return redirect('payroll_list')
#
#     messages.error(request, "Invalid request method.")
#     return redirect('payroll_list')
#
@login_required
def calculate_net_pay_all(request):
    calculate_payroll(request)
    messages.success(request, "Net pay calculated for all employees.")
    return redirect('payroll_list')


@login_required
def payroll_view(request):
    payslips = Payslip.objects.select_related('payroll__employee').all()
    context = {
        'page': 'payroll_list',
        'page_title': 'Payroll List',
        'payslips': payslips,
    }
    return render(request, 'payroll.html', context)


@login_required
def payroll_view_emp(request):
    employee = request.user.employee

    print("User:", request.user)  # Debugging print
    print("Employee:", employee)  # Debugging print

    payslips = Payslip.objects.filter(employee=employee)

    context = {
        'page': 'payroll_list',
        'page_title': 'Payroll List',
        'payslips': payslips,
    }
    return render(request, 'payroll_emp.html', context)


@login_required
def view_payroll(request, payslip_id):
    payslip = get_object_or_404(Payslip, id=payslip_id)
    return render(request, 'payslip.html', {'payslip': payslip})


@login_required
def view_emp_payslip(request, payslip_id):
    payslip = get_object_or_404(Payslip, id=payslip_id, employee__user=request.user)
    return render(request, 'payslip.html', {'payslip': payslip})


# @csrf_exempt
# @require_http_methods(["GET", "POST"])
# def scan_qr(request):
#     if request.method == 'POST':
#         employee_code = request.POST.get('employee_code')
#
#         if not employee_code:
#             messages.error(request, 'Employee code is required')
#             return redirect('scan_qr')  # Redirect back to the same page if there's an error
#
#         try:
#             employee = Employee.objects.get(employee_code=employee_code)
#         except ObjectDoesNotExist:
#             messages.error(request, 'Employee does not exist')
#             return redirect('scan_qr')
#
#         # Store the employee code in the session
#         request.session['employee_code'] = employee_code
#
#         # Redirect to the scan_face template
#         return redirect('scan_face')
#
#     return render(request, 'scan_qr.html')
@csrf_exempt
@require_http_methods(["GET", "POST"])
def scan_qr(request):
    if request.method == 'POST':
        employee_code = request.POST.get('employee_code')

        if not employee_code:
            messages.error(request, 'Employee code is required')
            return redirect('scan_qr')  # Redirect back to the same page if there's an error

        try:
            employee = Employee.objects.get(employee_code=employee_code)
        except ObjectDoesNotExist:
            messages.error(request, 'Employee does not exist')
            return redirect('scan_qr')


        request.session['employee_code'] = employee_code

        # Redirect to the scan_face template
        return redirect('scan_face')

    return render(request, 'scan_qr.html')


@csrf_exempt
@require_http_methods(["GET", "POST"])
def scan_face(request):
    if request.method == 'POST':
        facial_data = request.POST.get('facial_data')
        employee_code = request.session.get('employee_code')

        if not employee_code:
            messages.error(request, 'Employee code is missing')
            return redirect('scan_qr')

        try:
            employee = Employee.objects.get(employee_code=employee_code)
        except Employee.DoesNotExist:
            messages.error(request, 'Employee does not exist')
            return redirect('scan_qr')

        print(f"Received facial_data: {facial_data}")

        try:
            # Decode the uploaded facial data
            format, imgstr = facial_data.split(';base64,')
            ext = format.split('/')[-1]
            facial_data = base64.b64decode(imgstr)
            face_img = face_recognition.load_image_file(ContentFile(facial_data, name=f"temp_face.{ext}"))
        except ValueError:
            messages.error(request, 'Invalid facial data format')
            return redirect('scan_face')

        # Check the path where the facial data is stored
        facial_data_path = os.path.join(settings.MEDIA_ROOT, 'facial-data', f'{employee.employee_code}_facial_data.{ext}')
        print(f"Checking for facial data at: {facial_data_path}")

        if not os.path.exists(facial_data_path):
            messages.error(request, 'No facial data found for this employee')
            return redirect('scan_face')

        # Load employee's saved facial data
        employee_avatar = face_recognition.load_image_file(facial_data_path)

        # Compare faces
        face_encodings = face_recognition.face_encodings(face_img)
        if len(face_encodings) == 0:
            messages.error(request, 'No face detected in the captured image')
            return redirect('scan_face')

        face_encoding = face_encodings[0]
        employee_face_encodings = face_recognition.face_encodings(employee_avatar)

        if len(employee_face_encodings) == 0:
            messages.error(request, 'No face detected in the employee facial data')
            return redirect('scan_face')

        # Tolerance level for face comparison
        tolerance = 0.4
        matches = face_recognition.compare_faces([employee_face_encodings[0]], face_encoding, tolerance)
        face_distance = face_recognition.face_distance([employee_face_encodings[0]], face_encoding)

        print(f"Face matches: {matches}")
        print(f"Face distance: {face_distance}")

        if not matches[0] or face_distance[0] > tolerance:
            messages.error(request, 'Face does not match')
            return redirect('scan_face')

        today = timezone.now().date()

        # Get or create attendance record for the employee for today
        attendance, created = Attendance.objects.get_or_create(employee=employee, date=today)

        # Determine the current check-in/out type
        current_check_in_out = None
        for field in ['morning_check_in', 'morning_check_out', 'afternoon_check_in', 'afternoon_check_out']:
            if getattr(attendance, field, None) is None:
                current_check_in_out = field
                break

        if current_check_in_out is None:
            messages.error(request, 'No more check-in/out slots available')
            return redirect('scan_qr')

        # Set the check-in/out time
        setattr(attendance, current_check_in_out, timezone.now())
        attendance.save()

        if 'check_in' in current_check_in_out:
            success_message = f"You're timed in {employee.first_name} {(employee.middle_name or '')} {employee.last_name}."
        else:
            success_message = f"You're timed out {employee.first_name} {(employee.middle_name or '')} {employee.last_name}."
        messages.success(request, success_message)

        return redirect('scan_qr')

    return render(request, 'scan_face.html')


@login_required
def attendance_view(request):
    current_date = timezone.now().date()
    past_attendances = Attendance.objects.filter(date__lt=current_date)
    future_attendances = Attendance.objects.filter(date__gte=current_date)

    context = {
        'past_attendances': past_attendances,
        'future_attendances': future_attendances,
    }

    return render(request, 'attendance.html', context)


@login_required
def attendance_emp(request):
    current_user = request.user
    current_date = timezone.now().date()

    past_attendances = Attendance.objects.filter(date__lt=current_date)
    future_attendances = Attendance.objects.filter(date__gte=current_date)

    context = {
        'past_attendances': past_attendances,
        'future_attendances': future_attendances
    }

    return render(request, 'attendance_emp.html', context)
