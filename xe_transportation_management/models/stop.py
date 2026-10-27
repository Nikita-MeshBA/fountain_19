# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OpStop(models.Model):
    _name = "xe.stop"
    _order = "sequence asc"

    sequence = fields.Integer()
    name = fields.Char(size=64, required=True)
    partner_ids = fields.Many2many("res.partner", string="Person(s)")
    estimated_arrival_conf = fields.Float("Estimated Arrival Time")
    route_id = fields.Many2one("xe.route", "Route", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="School",
        default=lambda self: self.env["res.users"].browse([self.env.uid]).company_id,
    )

    @api.constrains("partner_ids")
    def check_capacity(self):
        total = 0
        for cap in self.route_id.stop_ids:
            total += len(cap.partner_ids)
        if total > self.route_id.vehicle_id.capacity:
            raise ValidationError(_("Vehicle capacity is over."))
