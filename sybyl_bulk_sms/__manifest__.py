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
    "name": "Xenesis Bulk SMS",
    "summary": "Send Bulk SMS",
    "version": "19.0.0.0.0",
    "license": "AGPL-3",
    "category": "SMS",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "author": "Sybyl",
    "depends": [
        "xenesis_school_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/ir_sequence_data.xml",
        "data/mobile_property_config.xml",
        "views/sms_gateway_view.xml",
        "views/sms_log_view.xml",
        "views/sms_templates_config.xml",
        "wizard/sms_template_views.xml",
    ],
}
