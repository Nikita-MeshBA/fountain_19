# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models, fields


class AttendanceWizard(models.TransientModel):
    _name = "attendance.report.wizard"
    _description = "Attendance Report Wizard"

    name = fields.Char("Student Attendance Report", default="Student Attendance Report")
    from_date = fields.Date(default=fields.Date.today())
    to_date = fields.Date(default=fields.Date.today())
    course_id = fields.Many2one("xe.course", "Class")
    term_id = fields.Many2one("xe.term", "Term")
    class_room_id = fields.Many2one("xe.classroom", string="Classroom")
    attendance_state = fields.Selection(
        [("present", "Present"), ("absent", "Absent"), ("all", "All")],
        default="all",
    )

    def print_attendance_report(self):
        data = {
            "from_date": self.from_date,
            "to_date": self.to_date,
            "formatted_from_date": self.from_date.strftime("%d-%m-%Y"),
            "formatted_to_date": self.to_date.strftime("%d-%m-%Y"),
            "course_id": self.course_id.id,
            "course": self.course_id.name,
            "class_room_id": self.class_room_id.id,
            "class_room": self.class_room_id.name,
            "attendance_state": self.attendance_state,
        }
        return self.env.ref(
            "xe_attendance_management.action_student_attendance"
        ).report_action(None, data=data)

    def print_attendance_report_excel(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "from_date": self.from_date,
                "to_date": self.to_date,
                "course_id": self.course_id.id,
                "class_room_id": self.class_room_id.id,
                "attendance_state": self.attendance_state,
            },
        }
        return self.env.ref(
            "xe_attendance_management.attendance_xlsx_report"
        ).report_action(self, data=data)
