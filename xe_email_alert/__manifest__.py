# -*- coding: utf-8 -*-
{
    "name": "Xenesis Email Alert",
    "summary": "Send Bulk Email",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Uncategorized",
    "depends": ["base", "xe_accounting_sms"],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "wizards/send_email_wizard.xml",
    ],
    "installable": True,
    "auto_install": False,
}
