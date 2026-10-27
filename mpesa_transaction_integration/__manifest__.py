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
    "name": "Xenesis Mpesa Integration",
    "version": "19.0.0.0",
    "summary": "Integration with Safaricom Paybill, Reconcile Mpesa Transactions, Invoice reconciliation, Payment Voucher reconciliation and auto reconciliation with student identifier, Xenesis",
    "sequence": 30,
    "description": """
        MPesa Transaction Integration
    """,
    "category": "Payment",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "license": "OPL-1",
    "depends": ["account", "sale_management", "report_xlsx", "web", "xenesis_school_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/account_journal_data.xml",
        "views/templates.xml",
        "views/res_config_settings_views.xml",
        "views/mpesacash_payment_view.xml",
        "views/account_journal_view.xml",
        "views/account_invoice_view.xml",
        "wizard/payment_reconcile.xml",
        "views/report_mpesa_templates.xml",
        "wizard/mpesa_transaction_report_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "https://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700",
            "/mpesa_transaction_integration/static/src/lib/daterangepicker/daterangepicker.css",
            "/mpesa_transaction_integration/static/src/lib/datatables/datatables.css",
            "/mpesa_transaction_integration/static/src/css/mpesacash_payment.css",
            "/mpesa_transaction_integration/static/src/lib/Chart/Chart.js",
            "/mpesa_transaction_integration/static/src/lib/datatables/datatables.js",
            "/mpesa_transaction_integration/static/src/lib/daterangepicker/daterangepicker.js",
            # '/mpesa_transaction_integration/static/src/js/mpesacash_payment.js',
        ],
        "web.assets_qweb": [
            "mpesa_transaction_integration/static/src/xml/mpesacash_payment.xml",
        ],
    },
}
