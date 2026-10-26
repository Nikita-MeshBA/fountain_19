# -*- coding: utf-8 -*-

from odoo import models, api, fields


class XeHeldExam(models.TransientModel):
    _name = "xe.held.exam"
    _description = "Held Exam"

    course_id = fields.Many2one("xe.course", "Class")
    academic_term_id = fields.Many2one("xe.academic.terms")
    term_id = fields.Many2one("xe.term", "Term")
    exam_id = fields.Many2one("xe.exam", "Exam")
    subject_id = fields.Many2one("xe.subject", "Subject")
    attendees_line_ids = fields.Many2many("xe.exam.attendees", string="Attendees")

    @api.model
    def default_get(self, fields):
        res = super(XeHeldExam, self).default_get(fields)
        active_id = self.env.context.get("active_id", False)
        exam = self.env["xe.exam"].browse(active_id)
        session = exam.session_id
        res.update(
            {
                "academic_term_id": session.academic_term_id.id,
                "course_id": session.course_id.id,
                "exam_id": active_id,
                "subject_id": exam.subject_id.id,
            }
        )
        return res

    def held_exam(self):
        for record in self:
            if record.attendees_line_ids:
                for attendee in record.attendees_line_ids:
                    attendee.status = "absent"
            record.exam_id.state = "held"
            return True
