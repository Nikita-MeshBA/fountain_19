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
    "name": "Subject wise Attendance",
    "summary": "Subject wise Attendance",
    "author": "Sybyl Cloud",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "category": "Uncategorized",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "depends": [
        "xenesis_school_base",
        "xe_attendance_management",
        "xe_fees_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/views.xml",
        "views/subject_registraion.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
