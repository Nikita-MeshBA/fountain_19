# -*- coding: utf-8 -*-


from odoo import models, fields


class OpPublisher(models.Model):
    _name = "xe.publisher"
    _description = "Publisher"

    name = fields.Char(required=True)
    address_id = fields.Many2one("res.partner")
    media_ids = fields.Many2many("xe.media", string="media(s)")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
