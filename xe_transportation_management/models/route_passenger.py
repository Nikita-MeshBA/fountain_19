# -*- coding: utf-8 -*-

from odoo import models, fields


class OpRoutePssenger(models.Model):
    _name = "xe.route.passenger"

    stop_id = fields.Many2one("xe.stop", "Stop", required=True)
    route_line_id = fields.Many2one(
        "xe.route.line", "Route Line", required=True, ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", "Passenger", required=True)
    present = fields.Boolean("Present/Absent")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    stop_ids = fields.Many2many("xe.stop", string="Stops")


class Student(models.Model):
    _inherit = "xe.student"

    stop_ids = fields.Many2many(
        "xe.stop", string="Stops", related="partner_id.stop_ids"
    )
