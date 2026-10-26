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
    "name": "Xenesis Lesson Planner",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Human Resources/Employees",
    "author": "Sybyl",
    "summary": "Manage CBC and 8-4-4 Scheme of work and lesson planner.",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": ["hr", "mail", "web", "xenesis_school_base", "xe_kenya_hr_payroll", "report_xlsx"],
    "data": [
        "security/xe_security.xml",
        "security/ir.model.access.csv",
        "views/res_company_view.xml",
        "views/cbc_lesson_planner_view.xml",
        "views/cbc_hr_employee_approval_view.xml",
        "wizards/lesson_plan_report_wizard_view.xml",
        "views/lesson_planner_timing_view.xml",
        "views/lesson_planner_view.xml",
        "reports/cbc_lesson_planner_report_views.xml",
        "reports/lesson_planner_report_views.xml",
        "reports/report_scheme_of_work.xml",
        "reports/report_menu.xml",
    ],
    "demo": [
        "demo/lesson_plan_header.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
