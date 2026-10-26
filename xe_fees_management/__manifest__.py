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
    "name": "Xenesis Fees Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Fees Management",
    "summary": "Manage Fee Types, Fee Structure, Invoice Generation",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": ["xenesis_school_base", "product", "account"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/cron.xml",
        "data/interview_fee_partner.xml",
        "views/fees_view.xml",
        "views/course_view.xml",
        "views/fees_type_view.xml",
        "views/fees_receipt_view.xml",
        "views/fees_structure_view.xml",
        "views/product_view.xml",
        "views/account_move_view.xml",
        "views/student_view.xml",
        "views/res_config_settings_view.xml",
        "wizard/fees_generation_wizard.xml",
        "wizard/fees_detail_report_wizard_view.xml",
        "views/menu_view.xml",
        "reports/report_menu.xml",
        "reports/new_fees_analysis.xml",
    ],
}
