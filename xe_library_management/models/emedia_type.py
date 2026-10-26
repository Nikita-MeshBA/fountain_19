# -*- coding: utf-8 -*-

import calendar
import json
from datetime import date

from odoo import models, fields


class OpMediaType(models.Model):
    _inherit = "xe.media.type"

    def _compute_issued(self):
        for media in self:
            medias = self.env["xe.media.unit"].search_count(
                [("media_type_id", "=", media.id), ("state", "in", ["issue"])]
            )
            media.issued = int(medias)

    def _compute_available(self):
        for media in self:
            medias = self.env["xe.media.unit"].search_count(
                [("media_type_id", "=", media.id), ("state", "in", ["available"])]
            )
            media.available = int(medias)

    def _compute_total_copies(self):
        for media in self:
            medias = self.env["xe.media.unit"].search_count(
                [("media_type_id", "=", media.id)]
            )
            media.total_copies = int(medias)

    def _compute_due_media_today(self):
        for media in self:
            today_due_media = self.env["xe.media.movement"].search_count(
                [
                    ("media_type_id", "=", media.id),
                    ("state", "=", "issue"),
                    ("return_date", "=", date.today()),
                ]
            )
            media.due_media_today = int(today_due_media)

    def _compute_due_media_month(self):
        for media in self:
            last_day = date.today().replace(
                day=calendar.monthrange(date.today().year, date.today().month)[1]
            )
            month_due_media = self.env["xe.media.movement"].search_count(
                [
                    ("state", "=", "issue"),
                    ("media_type_id", "=", media.id),
                    ("return_date", ">=", date.today().strftime("%Y-%m-01")),
                    ("return_date", "<=", last_day),
                ]
            )
            media.due_media_month = int(month_due_media)

    issued = fields.Integer(compute="_compute_issued")
    available = fields.Integer(compute="_compute_available")
    total_copies = fields.Integer(compute="_compute_total_copies")
    due_media_today = fields.Integer(
        "Due Media of Today", compute="_compute_due_media_today"
    )
    due_media_month = fields.Integer(
        "Due Media of Month", compute="_compute_due_media_month"
    )
    company_id = fields.Many2one(
        "res.company",
        string="School",
        default=lambda self: self.env.company,
    )
    kanban_dashboard_graph = fields.Text(compute="_compute_kanban_dashboard_graph")

    def _compute_kanban_dashboard_graph(self):
        for value in self:
            value.kanban_dashboard_graph = json.dumps(value.get_bar_graph_datas())

    def get_bar_graph_datas(self):
        for record in self:
            data = []
            for d in range(1, (fields.date.today().day) + 1):
                label = str(d)
                value = self.env["xe.media.movement"].search_count(
                    [
                        ("media_type_id", "=", record.id),
                        ("state", "in", ["issue"]),
                        ("issued_date", "=", fields.date.today().replace(day=d)),
                    ]
                )
                data.append({"label": label, "value": value and value or 0})
            return [{"values": data}]

    def create_new_media_type(self):
        action = self.env.ref("xe_library_management.act_open_xe_media_view").read()[0]
        action.update(
            {
                "context": "{'default_media_type_id': " + str(self.id) + "}",
                "views": [[False, "form"]],
            }
        )
        return action
