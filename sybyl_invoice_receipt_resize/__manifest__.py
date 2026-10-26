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
    "name": "Print Resized Invoice Receipt",
    "summary": "Print Resized Invoice Receipt, Xenesis",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Reporting",
    "depends": ["base", "account", "xe_admission_management"],
    "data": [
        "reports/new_external_layout.xml",
        "reports/invoice_receipt_report.xml",
        "reports/invoice_recipt_template.xml",
    ],
    "installable": True,
    "application": False,
}
