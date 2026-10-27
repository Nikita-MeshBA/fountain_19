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
    "name": "Bank Statement Reconciliation",
    "summary": """Bank Statement Reconciliation""",
    "description": """
        In Odoo, importing a bank statement will create journal entries for each statement line.
        In the case of our customers, it is not needed and they just need a screen to validate that
        all entries are present in the system. This module will allow the users to do that manually.
    """,
    "author": "Sybyl",
    "website": "www.sybyl.com, www.sybylcloud.com",
    "category": "Accounting/Accounting",
    "license": "OPL-1",
    "version": "19.0.0.0",
    "depends": ["account", "report_xlsx"],
    "data": [
        "security/ir.model.access.csv",
        "views/bank_statement_reconciliation.xml",
        "report/report.xml",
    ],
}
