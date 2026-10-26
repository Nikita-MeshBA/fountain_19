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
    "name": "Xenesis Assignment Management",
    "summary": "Create Assignment, Submit Asignment, Allocate Asignment. Manage creation of Assignments and assign to students",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "category": "Education Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "depends": ["base", "xenesis_school_base", "portal"],
    "data": [
        "security/xe_assignment_security.xml",
        "security/ir.model.access.csv",
        "data/email.xml",
        "views/xe_assignments.xml",
        "views/assignment_type.xml",
        "views/assignment_submissions.xml",
        "data/mark_done_cron.xml",
        "reports/assignment_submission_report.xml",
        "wizards/submission_report_wizard.xml",
    ],
    "installable": True,
    "auto_install": False,
}
