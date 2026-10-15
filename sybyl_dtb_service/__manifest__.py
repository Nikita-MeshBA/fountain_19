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
    "name": "Xenesis DTB Service",
    "version": "19.0.0.0.0",
    "summary": "Integration with Diamond Trust Bank, Reconcile DTB Transaction, Invoice Reconciliation, Payment Voucher Reconciliation and auto reconciliation with student identifier",
    "sequence": 0,
    "category": "Web",
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "license": "OPL-1",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "data/transaction_data.xml",
        "data/account_journal_data.xml",
        "views/transaction_views.xml",
        "views/account_invoice_view.xml",
        "views/account_journal_view.xml",
        "wizard/payment_reconcile.xml",
    ],
    "qweb": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
