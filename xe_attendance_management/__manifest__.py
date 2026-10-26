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
    "name": "Xenesis Student Attendance Management",
    "summary": "Mark Student Attendance, Create Attendance Sheets, Attendance Registers",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "category": "Education Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "hr",
        "xenesis_school_base",
        "xe_timetable_management",
        "report_xlsx",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/default_data.xml",
        "views/attendance_details.xml",
        "views/student_attendance.xml",
        "views/attendance_register.xml",
        "data/attendance_sheet_cron.xml",
        "views/student_profile.xml",
        "views/res_config_settings.xml",
        "views/remarks_type.xml",
        "wizard/attendance_report_wizard.xml",
        "wizard/attendance_summary_report_wizard.xml",
        "reports/attendance_report_xlsx.xml",
        "reports/attendance_report.xml",
    ],
    "installable": True,
    "auto_install": False,
}
