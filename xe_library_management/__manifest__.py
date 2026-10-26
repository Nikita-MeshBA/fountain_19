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
    "name": "Xenesis Library Management",
    "version": "19.0.0.0",
    "license": "OPL-1",
    "category": "Education",
    "sequence": 3,
    "summary": "Create Media, Media units, Media Types, Library Cards and manage Issuing and Returning of Media for students and Faculy",
    "complexity": "easy",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "depends": [
        "xenesis_school_base",
        "account",
        "xe_kenya_hr_payroll",
        "barcodes",
    ],
    "data": [
        "data/custom_paperformat.xml",
        "security/library_security.xml",
        "wizards/generate_media_units.xml",
        "wizards/issue_media_view.xml",
        "wizards/return_media_view.xml",
        "wizards/renew_media_view.xml",
        "wizards/reserve_media_view.xml",
        "wizards/lost_media.xml",
        "wizards/barcode_issue_media_view.xml",
        "views/media_unit_view.xml",
        "views/media_view.xml",
        "security/ir.model.access.csv",
        "report/report_media_barcode.xml",
        "report/report_library_card_barcode.xml",
        "report/report_student_library_card.xml",
        "report/report_menu.xml",
        "views/media_movement_view.xml",
        "views/media_purchase_view.xml",
        "views/media_queue_view.xml",
        "views/library_view.xml",
        "views/author_view.xml",
        "views/publisher_view.xml",
        "views/tag_view.xml",
        "views/media_type_view.xml",
        "views/student_view.xml",
        "views/faculty_view.xml",
        "views/library_barcode.xml",
        # "views/barcode_view.xml",
        "data/library_sequence.xml",
        "views/emedia_movement_view.xml",
        "views/library_dashboard_view.xml",
        "data/action_rule_data.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # '/xe_library_management/static/src/js/library_barcode.js',
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}
