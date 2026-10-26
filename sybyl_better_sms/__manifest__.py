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
    "name": "Xenesis Better SMS",
    "summary": "Better SMS Integration",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "SMS",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "author": "Sybyl",
    "depends": ["base", "sybyl_bulk_sms", "xe_accounting_sms", "account"],
    "data": ["views/sms_gateway_views.xml"],
    "installable": True,
    "application": False,
}
