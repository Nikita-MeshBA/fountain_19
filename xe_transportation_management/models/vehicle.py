# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OpVehicle(models.Model):
    _inherit = "fleet.vehicle"

    capacity = fields.Integer(required=True)
    company_id = fields.Many2one(
        "res.company",
        string="School",
        default=lambda self: self.env["res.users"].browse([self.env.uid]).company_id,
    )

    @api.constrains("capacity")
    def check_capacity(self):
        if self.capacity <= 0:
            raise ValidationError(_("Enter proper Capacity."))
