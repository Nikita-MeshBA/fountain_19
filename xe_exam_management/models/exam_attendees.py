# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _


class XeExamAttendees(models.Model):
    _name = "xe.exam.attendees"
    _description = "Exam Attendees"
    _rec_name = "student_id"

    comments = fields.Text()
    student_id = fields.Many2one("xe.student", required=True)
    status = fields.Selection(
        [("present", "Present"), ("absent", "Absent")], default="present", required=True
    )
    marks = fields.Integer()
    exam_id = fields.Many2one("xe.exam", required=True, ondelete="cascade")
    course_id = fields.Many2one("xe.course", "Class", readonly=True)
    # term_id = fields.Many2one("xe.term", "Term", readonly=True)
    room_id = fields.Many2one("xe.exam.room")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    state = fields.Selection(related="exam_id.state", store=True, readonly=True)
    subject_id = fields.Many2one(
        "xe.subject", related="exam_id.subject_id", store=True, readonly=True
    )
    start_time = fields.Datetime(
        related="exam_id.start_time", readonly=True, store=True
    )
    end_time = fields.Datetime(related="exam_id.end_time", readonly=True, store=True)
    evaluation_type = fields.Selection(
        "Exam Type",
        related="exam_id.session_id.course_id.evaluation_type",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "unique_attendees",
            "unique(student_id,exam_id)",
            "Attendee must be unique per exam.",
        )
    ]

    def write(self, values):
        if values:
            student_id = self.student_id and self.student_id.id
            exam_id = self.exam_id and self.exam_id.id
            result_line = (
                self.env["xe.result.line"].search(
                    [("student_id", "=", student_id), ("exam_id", "=", exam_id)]
                )
                or False
            )
            if result_line:
                raise ValidationError(
                    _("You cannot modify the line, result is already generated")
                )
        result = super(XeExamAttendees, self).write(values)
        return result

    @api.onchange("exam_id")
    def onchange_exam(self):
        self.course_id = self.exam_id.session_id.course_id
        # self.term_id = self.exam_id.session_id.term_id

    @api.constrains("marks")
    def _check_marks(self):
        for i in self:
            if i.marks < 0.0:
                raise ValidationError(_("Enter proper marks!"))

    @api.constrains("marks")
    def _check_constraint(self):
        for record in self:
            marks = record.marks
            max_marks = record.exam_id and record.exam_id.total_marks
            if record.evaluation_type != "1-3 CBC" and marks > max_marks:
                raise UserError(
                    _("Entered marks seems to be greater than Maximum Marks")
                )
