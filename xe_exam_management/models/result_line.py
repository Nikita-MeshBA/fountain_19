# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _


class XeResultLine(models.Model):
    _name = "xe.result.line"
    _description = "Result Line"
    _rec_name = "marks"

    marksheet_line_id = fields.Many2one("xe.marksheet.line", ondelete="cascade")
    exam_id = fields.Many2one("xe.exam", required=True)
    marks = fields.Integer(required=True)
    grade = fields.Char(readonly=True, compute="_compute_grade_new", store=True)
    student_id = fields.Many2one("xe.student", required=True)
    status = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")], compute="_compute_status", store=True
    )
    comments = fields.Text()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    rubrics = fields.Char(readonly=True, compute="_compute_rubrics", store=True)
    related_course_id = fields.Many2one(
        "xe.course",
        "Course",
        related="exam_id.session_id.course_id",
        store=True,
        readonly=True,
    )
    related_academic_term_id = fields.Many2one(
        "xe.academic.terms",
        related="exam_id.session_id.academic_term_id",
        store=True,
        readonly=True,
    )
    start_time = fields.Datetime(
        related="exam_id.start_time", readonly=True, store=True
    )
    end_time = fields.Datetime(related="exam_id.end_time", readonly=True, store=True)
    subject_id = fields.Many2one(
        "xe.subject", "Subject", related="exam_id.subject_id", store=True, readonly=True
    )
    total_marks = fields.Integer(
        related="exam_id.total_marks", store=True, readonly=True
    )
    evaluation_type = fields.Selection(
        "Exam Type",
        related="exam_id.session_id.course_id.evaluation_type",
        store=True,
        readonly=True,
    )

    @api.constrains("marks", "marks")
    def _check_marks(self):
        if self.marks < 0.0:
            raise ValidationError(_("Enter proper Marks or Percentage!"))

    @api.model
    def create(self, values):
        result = super(XeResultLine, self).create(values)
        exam_id = result.exam_id and result.exam_id.id
        student_id = result.student_id and result.student_id.id
        attendance_line = self.env["xe.exam.attendees"].search(
            [("student_id", "=", student_id), ("exam_id", "=", exam_id)]
        )
        if attendance_line:
            attendance_line = attendance_line[0]
        if not attendance_line:
            attendance_line = self.env["xe.exam.attendees"].create(
                {
                    "student_id": result.student_id.id,
                    "exam_id": result.exam_id.id,
                    "status": "present",
                    "marks": result.marks,
                    "comments": result.comments,
                }
            )
        comments = attendance_line.comments or ""
        result.write({"comments": comments})
        return result

    @api.depends("marks")
    def _compute_status(self):
        for record in self:
            record.status = "pass"
            if record.marks < record.exam_id.min_marks:
                record.status = "fail"

    @api.constrains("marks")
    def _check_constraint(self):
        for record in self:
            marks = record.marks
            max_marks = record.exam_id and record.exam_id.total_marks
            if record.evaluation_type != "1-3 CBC" and marks > max_marks:
                raise UserError(
                    _("Entered marks seems to be greater than Maximum Marks")
                )

    @api.depends("marks")
    def _compute_rubrics(self):
        for record in self:
            rubrics = (
                self.env["xe.rubrics.configuration"].search(
                    [("min_per", "<=", record.marks), ("max_per", ">=", record.marks)]
                )
                and self.env["xe.rubrics.configuration"].search(
                    [("min_per", "<=", record.marks), ("max_per", ">=", record.marks)]
                )[0]
                or False
            )
            if rubrics:
                record.rubrics = rubrics.code

    @api.depends("marks")
    def _compute_grade_new(self):
        for record in self:
            if record.evaluation_type:
                grades = (
                    self.env["xe.grade.configuration"].search(
                        [
                            ("min_per", "<=", record.marks),
                            ("max_per", ">=", record.marks),
                        ]
                    )
                    and self.env["xe.grade.configuration"].search(
                        [
                            ("min_per", "<=", record.marks),
                            ("max_per", ">=", record.marks),
                        ]
                    )[0]
                    or False
                )
                if grades:
                    record.grade = grades.result

    def write(self, values):
        if values:
            state = (
                self.marksheet_line_id
                and self.marksheet_line_id.marksheet_reg_id
                and self.marksheet_line_id.marksheet_reg_id.state
                or False
            )
            if state and state != "draft":
                raise ValidationError(
                    _("You cannot modify the record, since it is not in draft state.")
                )
        result = super(XeResultLine, self).write(values)
        return result
