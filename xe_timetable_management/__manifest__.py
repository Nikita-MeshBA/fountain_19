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
    "name": "Xenesis Time Table Management",
    "summary": "Create and Manage School Timetable",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "category": "Time Table Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "depends": ["base", "xenesis_school_base", "portal"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/timetable_session.xml",
        "views/xe_timings.xml",
        "views/session_lines.xml",
    ],
    "installable": True,
    "auto_install": False,
}
