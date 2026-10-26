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
    "name": "Xenesis Exam Management",
    "version": "17.0.0.0.0",
    "license": "AGPL-3",
    "category": "Education",
    "sequence": 3,
    "summary": "Create Exam Session, Exam, Marksheet Lines and print Report cards",
    "complexity": "easy",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": [
        "xenesis_school_base",
        "xe_admission_management",
    ],
    "data": [
        "security/xe_exam_security.xml",
        "security/ir.model.access.csv",
        "security/multicompany_security.xml",
        "views/res_partner_view.xml",
        "views/exam_attendees_view.xml",
        "views/exam_room_view.xml",
        "views/exam_session_view.xml",
        "views/exam_type_view.xml",
        "wizard/room_distribution_view.xml",
        "wizard/send_email_wizard.xml",
        "wizard/held_exam_view.xml",
        "views/exam_view.xml",
        "views/subject_view.xml",
        "views/marksheet_line_view.xml",
        "views/marksheet_register_view.xml",
        "views/grade_configuration_view.xml",
        "views/result_line_view.xml",
        "views/result_template_view.xml",
        "views/res_config_settings.xml",
        "report/report_ticket.xml",
        "report/student_marksheet.xml",
        "report/student_marksheet_line.xml",
        "report/report_menu.xml",
        "report/student_marksheet_new.xml",
        "report/new_external_layout.xml",
        "report/cbc_report_menu.xml",
        "report/cbc_summative_marksheet_report.xml",
        "report/cbc_combine_marksheet_line_report.xml",
        "report/cbc_session_combine_marksheet_line_report.xml",
        "report/report_cbc_session_wise.xml",
        "report/marksheet_line_session_wise.xml",
        "report/cbc_student_marksheet.xml",
        "report/cbc_student_marksheet_line.xml",
        "views/student_view.xml",
        "wizard/student_hall_tickets_wizard_view.xml",
        "views/grade_category_view.xml",
        "views/exam_menu.xml",
        "wizard/exam_analaysis_report_wizard.xml",
        "wizard/exam_attendee_report_wizard.xml",
        "wizard/confirm_exam_wizard.xml",
        "wizard/import_session_rubrics_wizard_view.xml",
        "wizard/add_exam_wizard_view.xml",
        "data/mail_template_data.xml",
        "views/terms_view.xml",
        "views/course_view.xml",
        "views/rubrics_code.xml",
        "views/rubrics_configuration_view.xml",
        "views/academic_terms_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/xe_exam_management/static/src/js/marksheet_line_form.js",
            "/xe_exam_management/static/src/js/marksheet_line_tree.js",
        ],
    },
    "images": [
        "static/description/xe_exam_management_banner.jpg",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
