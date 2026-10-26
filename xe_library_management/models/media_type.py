# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OpMediaType(models.Model):
    _name = "xe.media.type"
    _description = "Media Type"

    name = fields.Char(size=64, required=True)
    code = fields.Char(size=64, required=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    sequence_id = fields.Many2one("ir.sequence")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code") and self.search([("code", "=", vals.get("code")), ("company_id", "=", self.env.company.id)]):
                raise ValidationError(
                    _("Code %s already exists. Code should be unique per media type!" % (vals.get("code")))
                )
        return super(OpMediaType, self).create(vals_list)

    def write(self, vals):
        if vals.get("code") and self.search([("code", "=", vals.get("code")), ("company_id", "=", self.env.company.id)]):
            raise ValidationError(
                _("Code %s already exists. Code should be unique per media type!" % (vals.get("code")))
            )
        return super(OpMediaType, self).write(vals)