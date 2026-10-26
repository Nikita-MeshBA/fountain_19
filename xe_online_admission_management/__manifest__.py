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
    "name": "Xenesis Online Admission Management",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Education",
    "sequence": 3,
    "summary": "Manage Online Admission's",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": ["website", "xe_admission_management"],
    "data": [
        "views/enquiry_website_view.xml",
        "views/enquiry_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "xe_online_admission_management/static/src/js/admission_form.js"
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}
