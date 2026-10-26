# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models, _


class Student(models.Model):
    _inherit = "xe.student"

    def action_view_attendance(self):
        return {
            "name": _("Attendance Details"),
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": "xe.attendance.details",
            "target": "current",
            "domain": [
                ("student_id", "=", self.id),
                ("attendance_id.state", "=", "approved"),
            ],
        }
