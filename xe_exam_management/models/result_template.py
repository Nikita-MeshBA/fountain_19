# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class XeResultTemplate(models.Model):
    _name = "xe.result.template"
    _inherit = ["mail.thread"]
    _description = "Result Template"
    _rec_name = "name"

    exam_session_id = fields.Many2one(
        "xe.exam.session", "Exam Session", required=True, tracking=True
    )
    evaluation_type = fields.Selection(
        related="exam_session_id.evaluation_type", store=True, tracking=True
    )
    name = fields.Char(size=254, required=True, tracking=True)
    result_date = fields.Date(default=fields.Date.today(), tracking=True)
    grade_ids = fields.Many2many("xe.grade.configuration", string="Grade Configuration")
    state = fields.Selection(
        [("draft", "Draft"), ("result_generated", "Result Generated")],
        default="draft",
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.constrains("exam_session_id")
    def _check_exam_session(self):
        for record in self:
            for exam in record.exam_session_id.exam_ids:
                if exam.state != "done":
                    raise ValidationError(
                        _(
                            "For results to be generated, all exams must be in the done stage"
                        )
                    )
            result_template_count = self.env["xe.result.template"].search_count(
                [("exam_session_id", "=", record.exam_session_id.id)]
            )
            if result_template_count > 1:
                raise ValidationError(_("Result is already generated !!!"))

    @api.constrains("grade_ids")
    def _check_min_max_per(self):
        for record in self:
            count = 0
            for grade in record.grade_ids:
                for sub_grade in record.grade_ids:
                    if grade != sub_grade:
                        if (
                            sub_grade.min_per <= grade.min_per <= sub_grade.max_per
                        ) or (sub_grade.min_per <= grade.max_per <= sub_grade.max_per):
                            count += 1
            if count > 0:
                raise ValidationError(_("Percentage range conflict with other record."))

    def generate_result(self):
        for record in self:
            marksheet_reg_id = self.env["xe.marksheet.register"].create(
                {
                    "name": "Mark Sheet for %s" % record.exam_session_id.name,
                    "exam_session_id": record.exam_session_id.id,
                    "evaluation_type": record.exam_session_id.course_id.evaluation_type,
                    "generated_date": fields.Date.today(),
                    "generated_by_id": self.env.uid,
                    "state": "draft",
                    "result_template_id": record.id,
                }
            )
            student_dict = {}
            for exam in record.exam_session_id.exam_ids:
                for attendee in exam.attendees_line_ids:
                    result_line_id = self.env["xe.result.line"].create(
                        {
                            "student_id": attendee.student_id.id,
                            "exam_id": exam.id,
                            "marks": str(attendee.marks or 0),
                        }
                    )
                    if attendee.student_id.id not in student_dict:
                        student_dict[attendee.student_id.id] = []
                    student_dict[attendee.student_id.id].append(result_line_id)
            for student in student_dict:
                stud = self.env["xe.student"].sudo().browse(int(student))
                marksheet_line_id = self.env["xe.marksheet.line"].create(
                    {
                        "student_id": stud.id,
                        "marksheet_reg_id": marksheet_reg_id.id,
                        "classroom_id": stud.classroom_id.id,
                    }
                )
                for result_line in student_dict[student]:
                    result_line.marksheet_line_id = marksheet_line_id
            record.state = "result_generated"

    @api.model
    def create(self, values):
        result = super(XeResultTemplate, self).create(values)
        result.exam_session_id.state = "done"
        return result
