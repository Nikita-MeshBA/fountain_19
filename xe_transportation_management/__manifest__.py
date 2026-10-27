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
    "name": "Xenesis Transportation Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Education",
    "sequence": 3,
    "summary": "Manage Transportations",
    "complexity": "easy",
    "author": "Sybyl Cloud",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": [
        "xenesis_school_base",
        "xe_admission_management",
        "xe_fees_management",
        "fleet",
        "report_xlsx",
        "account",
    ],
    "data": [
        "security/transportation_security.xml",
        "security/ir.model.access.csv",
        "views/sequence.xml",
        "views/stop_view.xml",
        "views/route_line_view.xml",
        "views/stop_line_view.xml",
        "views/route_view.xml",
        "views/vehicle_view.xml",
        "views/student_view.xml",
        "views/fleet_vehicle_cost_views.xml",
        "views/transportation_menu.xml",
        "reports/report_transports.xml",
        "reports/transportation_details_report.xml",
        "wizards/transport_report_wizard.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
