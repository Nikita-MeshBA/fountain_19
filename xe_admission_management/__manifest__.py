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
    "name": "Xenesis Admission Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Admission Management",
    "summary": "Manage Enquiry, Application & Student Enrollement",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": [
        "xenesis_school_base",
        "calendar",
        "xe_fees_management",
        "account",
        "sale",
        "report_xlsx",
        "account_invoice_fixed_discount",
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "data/mail_template_data.xml",
        "data/create_invoice_cron.xml",
        "wizard/schdule_interview_wizard_view.xml",
        "wizard/pass_or_fail_reason_wizard.xml",
        "wizard/fail_reason_wizard.xml",
        "wizard/assign_employee_wizard.xml",
        "report/leaving_certificate_report.xml",
        "security/xe_security.xml",
        "security/ir.model.access.csv",
        "views/admission_view.xml",
        "views/application_view.xml",
        "views/student_view.xml",
        "wizard/admission_fee_wizard_view.xml",
    ],
}
