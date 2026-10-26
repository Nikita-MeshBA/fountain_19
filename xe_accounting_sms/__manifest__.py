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
    "name": "Xenesis Accounting  SMS",
    "summary": "Send SMS for Accounting",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "SMS",
    "depends": ["base", "xenesis_school_base", "sybyl_bulk_sms"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/sms_templates.xml",
        "views/templates.xml",
        "views/views.xml",
        "wizard/send_sms_wizard.xml",
    ],
    "installable": True,
    "application": False,
}
