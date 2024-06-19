from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

from .views import manage_payroll, save_payroll, create_user, attendance_emp, view_emp_payslip, view_payroll, \
    edit_payroll_info, save_facial_data, record_facial_data

urlpatterns = [
    path('scan_qr', views.scan_qr, name='scan_qr'),
    path('qr_code/', include('qr_code.urls', namespace="qr_code")),
    path('', views.login_page, name='login-page'),
    path('admin_page/', views.home, name='admin-page'),  # Ensure trailing slash
    path('employee/', views.employee_page, name='employee-page'),  # Ensure trailing slash
    path('employee_list/', views.employee_list, name='employee-list'),
    path('login/', views.login_page, name='login-page'),
    path('user_login/', views.login_user, name='login-user'),
    path('home/', views.home, name='home-page'),
    path('logout/', views.logout_user, name='logout'),

    path('add_employee/', views.manage_employee, name='add-employee'),

    path('edit_employee/<int:pk>/', views.manage_employee, name='edit-employee'),
    path('manage_employee/', views.manage_employee, name='manage-employee'),

    path('save_employee/', views.save_employee, name='save-employee'),
    path('view_card/<int:pk>/', views.view_card, name='view-card'),
    path('view_details/<str:code>/', views.view_details, name='view-details'),
    path('view_details/', views.view_details, name='scanned-code'),
    path('scanner/', views.view_scanner, name='view-scanner'),
    path('delete_employee/<int:pk>/', views.delete_employee, name='delete-employee'),
    path('scan/', views.scan_qr, name='scan_qr'),

    path('payroll/', views.payroll_view, name='payroll-list'),
    path('add_payroll/<int:employee_pk>/', views.manage_payroll, name='add-payroll'),
    path('add_payroll/<int:employee_pk>/', manage_payroll, name='add-payroll'),
    path('save_payroll/', views.save_payroll, name='save-payroll'),

    path('scan/face/', views.scan_face, name='scan_face'),

    path('payroll/view/<int:payslip_id>/', views.view_payroll, name='view_payroll'),
    path('calculate_net_pay_all', views.calculate_payroll, name='calculate_net_pay_all'),
    path('create-employee/', views.manage_employee, name='create-employee'),


    path('attendance/', views.attendance_view, name='attendance-list'),


    path('view_payroll_info/<int:employee_pk>/', views.manage_payroll, name='view_payroll_info'),
    path('add_payroll/<int:employee_pk>/', views.manage_payroll, name='add-payroll'),
    path('save_payroll/', views.save_payroll, name='save_payroll'),
    path('payroll_list/', views.payroll_view, name='payroll_list'),


    path('edit_payroll/<int:employee_pk>/', views.edit_payroll, name='edit-payroll'),

    path('edit_payroll_info/<int:employee_pk>/', views.edit_payroll, name='edit_payroll_info'),

    path('edit_payroll_info/<int:employee_pk>/', edit_payroll_info, name='edit-payroll-info'),



    path('manage_employee/<int:pk>/', views.manage_employee, name='manage_employee'),
    path('manage_employee/<int:pk>/add_payroll/', views.manage_employee, {'add_payroll': True},name='add_payroll'),
    path('fetch_employee_profile', views.fetch_employee_profile, name='fetch_employee_profile'),
    path('get_employees/', views.get_employees, name='get-employees'),

    path('create_user/<int:employee_id>/', create_user, name='create_user'),
    path('get_employees/', views.get_employees, name='get_employees'),
    path('attendance_emp/', views.attendance_emp, name='attendance_emp'),

    path('payslip/view/<int:payslip_id>/', views.view_emp_payslip, name='view_payslip'),
    path('payroll_emp/', views.payroll_view_emp, name='payroll-list-emp'),

    #facial

    path('record-facial-data/<int:employee_id>/', record_facial_data, name='record-facial-data'),
    path('save-facial-data/', save_facial_data, name='save-facial-data'),





] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
