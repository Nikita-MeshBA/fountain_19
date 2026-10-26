#################################################################################
# Author      : Sybyl Cloud (www.sybyl.com, www.sybylcloud.com)
# Copyright(c): 2020-Present Sybyl Cloud.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
##################################################################
{
    "name": "Xenesis Kenya HR Payroll",
    "version": "19.0.0.0.1",
    "category": "Human Resources",
    "summary": "Manage Payslips, Send Payslips via email, Payroll Reports, Batch Payslips",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "license": "AGPL-3",
    "depends": [
        "xenesis_school_base",
        "hr_payroll_community",
        "hr_attendance",
        "report_xlsx",
        "hr_expense",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/hr_payroll_data.xml",
        "data/hr_employee_sequence.xml",
        "data/service_cron.xml",
        "data/hr_payslip_mail_template.xml",
        "data/employee_menu_server_action.xml",
        "views/employee_salary_grade.xml",
        "views/company_views.xml",
        "views/hr_views.xml",
        "views/hr_contract_views.xml",
        "views/hr_insurance_scheme_views.xml",
        "views/hr_life_insurance_views.xml",
        "views/hr_payslip.xml",
        "views/hr_expense_views.xml",
        "views/hr_employee_views.xml",
        "reports/employee_id_report_views.xml",
        "reports/student_id_report_views.xml",
        "reports/nita_xlsx_report.xml",
        "reports/nhif_report.xml",
        "reports/nssf_report.xml",
        "reports/ms_report.xml",
        "reports/paye_report.xml",
        "reports/salary_template_report.xml",
        "reports/insurance_report.xml",
        "reports/bknetsal_xlsx_report_report.xml",
        "views/res_config_settings_views.xml",
        "wizard/nssf.xml",
        "wizard/nita_report_wizard.xml",
        "wizard/monthly_salary_report_wizard.xml",
        "wizard/nhif.xml",
        "wizard/paye_report_wizard.xml",
        "wizard/salary_template.xml",
        "wizard/p9.xml",
        "wizard/insurance.xml",
        "wizard/banknetsalary_report_wizard.xml",
        "wizard/shif_deduction_report.xml",
    ],
    "images": ["static/src/img/kenya_revenue_authority_logo.png"],
    "installable": True,
    "auto_install": False,
    "application": True,
}
