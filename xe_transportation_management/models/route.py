# -*- coding: utf-8 -*-
from odoo import models, fields


class OpRoute(models.Model):
    _name = "xe.route"

    name = fields.Char(size=64, required=True)
    stop_ids = fields.One2many("xe.stop", "route_id", string="Stops")
    cost = fields.Float()
    vehicle_id = fields.Many2one("fleet.vehicle", "Vehicle", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="School",
        default=lambda self: self.env["res.users"].browse([self.env.uid]).company_id,
    )
