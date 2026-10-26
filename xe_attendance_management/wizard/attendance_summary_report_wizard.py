# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models, fields


class AttendanceSummaryWizard(models.TransientModel):
    _name = "attendance.summary.report.wizard"
    _description = "Attendance Summary Report Wizard"

    name = fields.Char("Student Attendance Report", default="Student Attendance Report")
    from_date = fields.Date(default=fields.Date.today())
    to_date = fields.Date(default=fields.Date.today())
    course_id = fields.Many2one("xe.course", "Class")
    class_room_id = fields.Many2one("xe.classroom", string="Classroom")

    def print_attendance_report_excel(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "from_date": self.from_date,
                "to_date": self.to_date,
                "course_id": self.course_id.id,
                "class_room_id": self.class_room_id.id,
            },
        }
        return self.env.ref(
            "xe_attendance_management.attendance_summary_xlsx_report"
        ).report_action(self, data=data)
