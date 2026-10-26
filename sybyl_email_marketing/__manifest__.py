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
    "name": "Xenesis Email Marketing",
    "summary": "Send Bulk Email",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "Email",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "author": "Sybyl",
    "depends": [
        "base",
        "mass_mailing",
        "xenesis_school_base",
    ],
    "data": [
        "views/mailing_list_view_inherit.xml",
    ],
    "installable": True,
    "application": False,
}
