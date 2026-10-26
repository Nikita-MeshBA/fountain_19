# -*- coding: utf-8 -*-

from odoo import models, fields


class DocumentType(models.Model):
    _name = "document.type"
    _description = "Document Type"
    _rec_name = "name"
    _inherit = "mail.thread"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
