# -*- coding: utf-8 -*-
from odoo import models, fields


class FeeReceipt(models.Model):
    _name = "fee.receipt"
    _description = "fee receipt"
    _rec_name = "name"

    name = fields.Char(size=32, required=True)
    notes = fields.Text()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        ("unique_receipt_name_id", "unique(name)", "Name should be unique per Receipt!")
    ]
