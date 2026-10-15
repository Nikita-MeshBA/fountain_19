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
    "name": "Internal Product Request",
    "summary": """Internal Product Request""",
    "author": "Sybyl Cloud",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "category": "Inventory",
    "version": "19.0.0.0.0",
    "license": "OPL-1",
    "depends": ["base", "stock"],
    "data": [
        "data/stock_locations.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/product_request.xml",
    ],
}
