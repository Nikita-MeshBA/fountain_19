# -*- coding: utf-8 -*-
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
    "name": "Xenesis Visitor Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Education",
    "sequence": 3,
    "summary": "Manage School Visitors",
    "complexity": "easy",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": ["xenesis_school_base", "xe_accounting_sms"],
    "data": [
        "data/mail_template_data.xml",
        "data/template_data.xml",
        "security/visitor_security.xml",
        "security/ir.model.access.csv",
        "reports/report_menu.xml",
        "reports/student_gate_pass_report.xml",
        "reports/visitor_gate_pass_report.xml",
        "wizards/purpose_type_wizard_view.xml",
        "wizards/send_sms_visitor.xml",
        "wizards/send_email_visitor.xml",
        "reports/purpose_type_report.xml",
        "reports/employee_wise_report.xml",
        "reports/student_pass_wise_report.xml",
        "wizards/employee_wise_wizard_view.xml",
        "wizards/student_pass_wise_wizard_view.xml",
        "views/visitor_pass_view.xml",
        "views/student_pass_view.xml",
        "views/purpose_type_view.xml",
        "views/document_type_view.xml",
        "views/res_config_settings_view.xml",
        "views/visitor_menu.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
