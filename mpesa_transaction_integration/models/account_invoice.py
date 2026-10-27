# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models, fields, _


class AccountInvoice(models.Model):
    _inherit = "account.move"
    reg_payment = fields.Float("Register Payment")

    def button_mpesa_cash_entries(self):
        return {
            "name": _("Mpesa Cash Transaction"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "mpesa.payment.transaction",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("invoice_id", "in", self.ids)],
        }
