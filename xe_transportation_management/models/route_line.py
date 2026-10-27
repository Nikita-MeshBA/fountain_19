# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api


class XeRouteLine(models.Model):
    _name = "xe.route.line"
    _description = "Trips"
    _inherit = ["mail.thread"]

    name = fields.Char(size=64, readonly=True)
    route_id = fields.Many2one("xe.route", "Route", required=True)
    route_type = fields.Selection(
        [("pickup", "Pickup"), ("drop", "Drop")], required=True
    )
    route_stop_ids = fields.One2many(
        "xe.route.stop.line", "route_line_id", string="Stops"
    )
    route_passenger_ids = fields.One2many(
        "xe.route.passenger", "route_line_id", string="Passenger"
    )
    route_date = fields.Date(
        "Date", required=True, default=lambda self: fields.Date.today()
    )
    start_time = fields.Float(required=True, tracking=True)
    driver_id = fields.Many2one(
        "res.partner",
        related="route_id.vehicle_id.driver_id",
        required=True,
        string="Driver",
        tracking=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("start", "Start"), ("end", "End")], default="draft"
    )
    company_id = fields.Many2one(
        "res.company",
        string="School",
        default=lambda self: self.env["res.users"].browse([self.env.uid]).company_id,
    )

    @api.onchange("route_id")
    def onchange_route_id(self):
        self.route_stop_ids = False
        self.route_passenger_ids = False

    def start_trip(self):
        self.state = "start"

    def end_trip(self):
        self.state = "end"

    @api.model
    def create(self, vals):
        route = self.env["xe.route"].browse([vals["route_id"]])
        x = self.env["ir.sequence"].next_by_code("xe.route.line") or ""
        seq = " (%s)" % x
        route_date = datetime.strptime(vals.get("route_date", False), "%Y-%m-%d")
        vals["name"] = route.name + " " + route_date.strftime("%d-%m-%Y") + seq
        return super(XeRouteLine, self).create(vals)

    def create_route_stop_line(self):
        for route in self:
            for stop in route.route_id.stop_ids:
                if stop.id not in [x.stop_id.id for x in route.route_stop_ids]:
                    self.env["xe.route.stop.line"].create(
                        {"route_line_id": route.id, "stop_id": stop.id}
                    )
                for passenger in stop.partner_ids:
                    if passenger.id not in [
                        p.partner_id.id for p in route.route_passenger_ids
                    ]:
                        self.env["xe.route.passenger"].create(
                            {
                                "route_line_id": route.id,
                                "partner_id": passenger.id,
                                "present": True,
                                "stop_id": stop.id,
                            }
                        )
