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
    "name": "Xenesis Hostel Management",
    "version": "19.0.0.0.0",
    "category": "Education Management",
    "summary": "Hostel Management, Manage Beds, Rooms, Floors, Amenities, Student Vacancy, Hostel Admission's",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "license": "AGPL-3",
    "depends": ["hr", "xe_admission_management", "xenesis_school_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/ir_sequence.xml",
        "views/hostel_views.xml",
        "views/hostel_admission_views.xml",
        "views/hostel_room_views.xml",
        "views/hostel_floor_views.xml",
        "views/hostel_assets_views.xml",
        "views/hostel_member_leaves_views.xml",
        "views/hostel_bed_views.xml",
        "views/hostel_bed_category_views.xml",
        "views/menu.xml",
        "views/student_views.xml",
        "views/application_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
