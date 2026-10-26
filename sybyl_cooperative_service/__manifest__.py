# -*- coding: utf-8 -*-
{
    "name": "Xenesis Cooperative Service",
    "summary": "Integration with Cooperative Bank, Reconcile Cooperative Bank Transaction, Invoice Reconciliation, Payment Voucher Reconciliation and auto reconciliation with student identifier",
    "author": "Sybyl",
    "website": "http://www.sybylcloud.com",
    "category": "Uncategorized",
    "version": "19.0.0.1",
    "sequence": "1",
    "license": "LGPL-3",
    "depends": [
        "account",
        "xenesis_school_base",
    ],
    "data": [
        "data/account_data.xml",
        "data/ir_cron_data.xml",
        "security/ir.model.access.csv",
        "views/coop_bank_log_view.xml",
        "views/coop_bank_transaction_views.xml",
        "wizard/payment_reconcile.xml",
    ],
    "application": True,
}
