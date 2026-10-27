# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mpesa_api_key = fields.Char(
        string="MpesaCash Api Key",
        default="test",
        config_parameter="mpesa_transaction_integration.mpesa_api_key",
    )
    mpesa_secret = fields.Char(
        help="Realex Shared Secret",
        default="secret",
        config_parameter="mpesa_transaction_integration.mpesa_secret",
    )
    is_reconcile = fields.Boolean(
        "Reconciliation Payment Methods",
        config_parameter="mpesa_transaction_integration.is_reconcile",
    )
    transaction_by = fields.Selection(
        [
            ("invoice_no", "Reconcile with Invoice Number"),
            ("grn", " Reconcile with Admission Number"),
        ],
        string="Transaction Mode",
        config_parameter="mpesa_transaction_integration.transaction_by",
    )
