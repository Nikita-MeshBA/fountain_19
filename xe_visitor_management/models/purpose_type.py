# -*- coding: utf-8 -*-

from odoo import models, fields


class PurposeType(models.Model):
    _name = "purpose.type"
    _rec_name = "name"
    _inherit = "mail.thread"
    _description = "Purpose Type"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
