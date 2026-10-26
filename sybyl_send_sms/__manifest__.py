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
    "name": "Sybyl Send SMS",
    "summary": "This App has the ability to send SMS using Send Sms API",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "author": "Sybyl",
    "company": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "category": "Tools",
    "depends": ["base", "account", "xenesis_school_base"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/template_data.xml",
        "views/base_config.xml",
        "views/account_invoice.xml",
        "wizard/send_sms_wizard.xml",
        "views/sms_gateway_view.xml",
        "views/sms_log_view.xml",
        "wizard/sms_log_wizard.xml",
        "views/sms_template_views.xml",
    ],
    "images": [
        "static/description/sms-invoice-banner.png",
    ],
    "installable": True,
    "application": False,
}
