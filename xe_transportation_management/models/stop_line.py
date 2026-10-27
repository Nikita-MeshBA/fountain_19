# -*- coding: utf-8 -*-
from odoo import models, fields, api


class OpRouteStopLine(models.Model):
    _name = "xe.route.stop.line"

    sequence = fields.Integer(related="stop_id.sequence", string="Sequence")
    stop_id = fields.Many2one("xe.stop", "Stop")
    estimated_time = fields.Float(
        compute="_compute_estimated_time", string="Estimated Arrival"
    )
    route_line_id = fields.Many2one("xe.route.line", "Route Line", ondelete="cascade")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.depends("stop_id.estimated_arrival_conf", "route_line_id.start_time")
    def _compute_estimated_time(self):
        for stop in self:
            stop.estimated_time = (
                stop.route_line_id.start_time + stop.stop_id.estimated_arrival_conf
            )
