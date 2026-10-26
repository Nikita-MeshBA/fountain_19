# -*- coding: utf-8 -*-

from odoo import models, fields


class XenesisAuthor(models.Model):
    _name = "xe.author"
    _description = "Author"

    name = fields.Char(size=128, required=True)
    # old field
    address = fields.Many2one("res.partner")
    # new field
    address_id = fields.Many2one("res.partner")
    media_ids = fields.Many2many("xe.media", string="media(s)")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
