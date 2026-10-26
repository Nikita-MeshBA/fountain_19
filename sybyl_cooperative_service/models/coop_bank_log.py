# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CoopBankLog(models.Model):
    _name = "coop.bank.log"
    _description = "Cooperative Bank Transaction Log"
    _order = "id desc"

    name = fields.Char("Request", readonly=True)
    response = fields.Char(readonly=True)
    url_endpoint = fields.Char(readonly=True)
    coop_bank_transaction_id = fields.Many2one("coop.bank.transaction", readonly=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.user.company_id, readonly=True
    )
    student_id = fields.Many2one("xe.student")
    invoice_id = fields.Many2one("account.move")
