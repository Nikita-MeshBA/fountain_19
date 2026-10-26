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
    "name": "Xenesis RFID Integration",
    "version": "19.0.0.0.0",
    "summary": """Sybyl RFID Integration""",
    "sequence": 1,
    "category": "Web",
    "author": "Sybyl Cloud",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "license": "OPL-1",
    "depends": ["account","xenesis_school_base"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/session_dashboard.xml",
        "views/device_view.xml",
        "views/card_view.xml",
        "views/rfid_logs_view.xml",
        "views/session_view.xml",
        "views/menu_item.xml",
        "views/res_config_setting.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sybyl_rfid_integration/static/src/js/student_detail_dialog.js",
            "sybyl_rfid_integration/static/src/scss/dialog_style.scss",
            "sybyl_rfid_integration/static/src/xml/student_detail_view.xml",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}
