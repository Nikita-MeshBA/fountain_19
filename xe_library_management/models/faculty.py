# -*- coding: utf-8 -*-

from odoo.exceptions import UserError

from odoo import models, fields, _


class XenesisFaculty(models.Model):
    _inherit = "hr.employee"

    library_card_id = fields.Many2one("xe.library.card", "Library Card")
    media_movement_lines_ids = fields.One2many(
        "xe.media.movement", "faculty_id", "Movements"
    )

    def action_library_card(self):
        card_type = (
            self.env["xe.library.card.type"]
            .search([("type", "=", "others")], limit=1)
            .id
        )
        if not card_type:
            raise UserError("Library Card Type is not configured for Others")
        ctx = {}
        ctx.update(
            {
                "default_number": self.employee_no,
                "default_faculty_id": self.id,
                "default_library_card_type_id": card_type,
            }
        )
        return {
            "name": _("Library Card"),
            "view_mode": "form",
            "res_model": "xe.library.card",
            "type": "ir.actions.act_window",
            "context": ctx,
        }

    def create_card_act(self):
        active_ids = self._context.get("active_ids")
        employees = self.env["hr.employee"].browse(active_ids)
        card_type = (
            self.env["xe.library.card.type"]
            .search([("type", "=", "others")], limit=1)
            .id
        )
        if not card_type:
            raise UserError("Library Card Type is not configured for Others")
        card_obj = self.env["xe.library.card"]
        for emp in employees:
            if not emp.library_card_id:
                library_vals = {
                    "number": emp.employee_no,
                    "faculty_id": emp.id,
                    "library_card_type_id": card_type,
                }
                card_obj.create(library_vals)

    def action_view_media_movement(self):
        media_movement_ids = self.env["xe.media.movement"].search(
            [("faculty_id", "=", self.id), ("state", "=", "issue")]
        )
        return {
            "name": "Media Movements",
            "view_mode": "list,form",
            "view_id": False,
            "domain": [("id", "in", media_movement_ids.ids)],
            "res_model": "xe.media.movement",
            "views": [
                (
                    self.env.ref(
                        "xe_library_management.view_xe_media_movement_tree"
                    ).id,
                    "tree",
                )
            ],
            "type": "ir.actions.act_window",
            "flags": {"action_buttons": False},
        }
