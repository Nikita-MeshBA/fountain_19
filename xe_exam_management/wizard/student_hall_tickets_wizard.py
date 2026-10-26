# -*- coding: utf-8 -*-

from odoo import models, fields


class StudentHallTicket(models.TransientModel):
    _name = "student.hall.ticket"
    _description = "Student Hall Ticket Wizard"

    exam_session_id = fields.Many2one("xe.exam.session", "Exam Session", required=True)

    def print_report(self):
        data = self.read(["exam_session_id"])[0]
        return self.env.ref(
            "xe_exam_management.action_student_hall_ticket_report"
        ).report_action(self, data=data)
