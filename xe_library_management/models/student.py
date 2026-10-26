# -*- coding: utf-8 -*-

from odoo.exceptions import UserError

from odoo import models, fields, _


class OpStudent(models.Model):
    _inherit = "xe.student"

    library_card_id = fields.Many2one("xe.library.card")
    media_movement_lines_ids = fields.One2many(
        "xe.media.movement", "student_id", "Movements"
    )

    def action_library_card(self):
        ctx = {}
        card_type = (
            self.env["xe.library.card.type"]
            .search([("type", "=", "student")], limit=1)
            .id
        )
        if not card_type:
            raise UserError(_("Library Card Type is not configured for Student"))
        ctx.update(
            {
                "default_number": self.roll_number,
                "default_student_id": self.id,
                "default_course_id": self.course_id.id,
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
        students = self.env["xe.student"].browse(active_ids)
        card_type = (
            self.env["xe.library.card.type"]
            .search([("type", "=", "student")], limit=1)
            .id
        )
        if not card_type:
            raise UserError(_("Library Card Type is not configured for Student"))
        card_obj = self.env["xe.library.card"]
        for student in students:
            if not student.library_card_id:
                library_vals = {
                    "number": student.roll_number,
                    "student_id": student.id,
                    "course_id": student.course_id.id,
                    "library_card_type_id": card_type,
                }
                card_obj.create(library_vals)

    def action_view_media_movement(self):
        media_movement_ids = self.env["xe.media.movement"].search(
            [("student_id", "=", self.id), ("state", "=", "issue")]
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
