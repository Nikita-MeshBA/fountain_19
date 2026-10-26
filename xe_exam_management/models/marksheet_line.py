# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _


class XeMarksheetLine(models.Model):
    _name = "xe.marksheet.line"
    _description = "Marksheet Line"
    _rec_name = "student_id"

    def check_report_new(self):
        data = {}
        return self.env.ref("xe_exam_management.report_marksheetline").report_action(
            self, data=data
        )

    def get_all_emails(self, student_obj):
        emails = student_obj.email
        parent_objs = self.env["xe.student.parent"].search(
            [("student_id", "=", student_obj.id)]
        )
        parent_ids = parent_objs.mapped("parent_id")
        for parent in parent_ids:
            parent_email = parent.partner_id.email if parent.partner_id.email else ""
            if parent_email:
                emails = emails + "," + parent_email
        return emails

    def action_marksheet_report_sent(self):
        self.ensure_one()
        all_emails = self.get_all_emails(self.student_id)
        if not all_emails:
            raise UserError(
                _("to email not found for the student %s") % self.student_id.name
            )
        template = self.env.ref("xe_exam_management.email_template_report_card", False)
        template.write({"email_to": all_emails})
        template.with_context(
            default_model="xe.marksheet.line",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_email_to=all_emails,
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
        ).send_mail(self.id, force_send=True)

    marksheet_reg_id = fields.Many2one("xe.marksheet.register", "Marksheet Register")
    evaluation_type = fields.Selection(
        "Exam Type",
        related="exam_session_id.course_id.evaluation_type",
        store=True,
        readonly=True,
    )
    student_id = fields.Many2one("xe.student", required=True)
    result_line_ids = fields.One2many("xe.result.line", "marksheet_line_id", "Results")
    total_marks = fields.Integer(compute="_compute_total_marks")
    percentage = fields.Float(compute="_compute_percentage")
    grade = fields.Char(readonly=True, compute="_compute_grade")
    status = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")], compute="_compute_status"
    )
    exam_session_id = fields.Many2one(
        "xe.exam.session",
        related="marksheet_reg_id.exam_session_id",
        store=True,
        readonly=True,
    )
    generated_date = fields.Date(
        related="marksheet_reg_id.generated_date", store=True, readonly=True
    )
    register_state = fields.Selection(
        related="marksheet_reg_id.state", store=True, readonly=True
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    head_master_comment = fields.Html("Headmaster Comment")
    academic_year_id = fields.Many2one(
        "xe.academic.year", related="exam_session_id.academic_year_id"
    )
    academic_term_id = fields.Many2one(
        "xe.academic.terms",
        related="exam_session_id.academic_term_id",
        store=True,
        readonly=True,
    )
    exam_ids = fields.Many2many("xe.exam")
    course_id = fields.Many2one(
        "xe.course",
        related="exam_session_id.course_id",
        store=True,
        readonly=True,
    )

    extra_curr_comment = fields.Text("Extra-Curricular Comments")
    head_teacher_comment = fields.Text("Head Teacher Comments")
    classroom_id = fields.Many2one("xe.classroom")

    @api.constrains("total_marks", "percentage")
    def _check_marks(self):
        if (self.total_marks < 0.0) or (self.total_per < 0.0):
            raise ValidationError(_("Enter proper marks or percentage!"))

    @api.depends("result_line_ids.marks")
    def _compute_total_marks(self):
        for record in self:
            record.total_marks = sum([int(x.marks) for x in record.result_line_ids])

    @api.depends("total_marks")
    def _compute_percentage(self):
        for record in self:
            total_exam_marks = sum(
                [int(x.exam_id.total_marks) for x in record.result_line_ids]
            )
            record.percentage = int(
                round(
                    record.total_marks
                    and (100 * record.total_marks) / total_exam_marks
                    or 0.0
                )
            )

    @api.depends("percentage")
    def _compute_grade(self):
        for record in self:
            record.grade = False
            if record.evaluation_type == "grade":
                grades = record.marksheet_reg_id.result_template_id.grade_ids
                for grade in grades:
                    if grade.min_per <= record.percentage <= grade.max_per:
                        record.grade = grade.result

    @api.depends("result_line_ids.status")
    def _compute_status(self):
        for record in self:
            record.status = "pass"
            for result in record.result_line_ids:
                if result.status == "fail":
                    record.status = "fail"

    @api.model
    def get_evaluation_type(self, active_id):
        record = self.browse(active_id)
        return record.evaluation_type

    @api.onchange("exam_session_id")
    def _compute_exam_ids(self):
        if self.exam_session_id:
            self.exam_ids = False
            exam_ids = self.env["xe.exam"].search(
                [("session_id", "=", self.exam_session_id.id)]
            )
            self.exam_ids = [(6, 0, exam_ids.ids)]

    @api.depends("result_line_ids.marks")
    def _compute_total_marks(self):
        for record in self:
            result_line_ids = record.result_line_ids
            total_marks = 0
            for line in result_line_ids:
                parent_subject_id = (
                    line.subject_id
                    and line.subject_id.parent_id
                    and line.subject_id.parent_id.id
                    or False
                )
                if not parent_subject_id:
                    total_marks = total_marks + line.marks
            record.total_marks = total_marks

    @api.depends("total_marks")
    def _compute_percentage(self):
        for record in self:
            result_line_ids = record.result_line_ids
            total_exam_marks = 0
            for line in result_line_ids:
                parent_subject_id = (
                    line.subject_id
                    and line.subject_id.parent_id
                    and line.subject_id.parent_id.id
                    or False
                )
                if not parent_subject_id:
                    total_exam_marks = total_exam_marks + line.exam_id.total_marks
            record.percentage = int(
                round(
                    record.total_marks
                    and (100 * record.total_marks) / total_exam_marks
                    or 0.0
                )
            )

    @api.depends("result_line_ids.status", "percentage")
    def _compute_status(self):
        for record in self:
            record.status = "pass"
            if record.percentage < 40:
                record.status = "fail"

    def check_report(self):
        data = {}
        data["form"] = self.read(["id"])[0]
        marksheet_line_obj = self.browse(self.read(["id"])[0]["id"])
        marksheet_reg_id = (
            marksheet_line_obj.marksheet_reg_id
            and marksheet_line_obj.marksheet_reg_id.id
            or False
        )
        data["marksheet_reg_id"] = marksheet_reg_id
        data["marksheet_line_id"] = self.read(["id"])[0]["id"]
        data["evaluation_type"] = marksheet_line_obj.evaluation_type
        data["course_name"] = (
            marksheet_line_obj.course_id and marksheet_line_obj.course_id.name
        )
        return self.env.ref("xe_exam_management.report_marksheet").report_action(
            self, data=data
        )

    def button_print(self):
        pass

    def button_cbc_marksheet_line_report(self):
        if self.env.user.has_group('xe_exam_management.group_rubrics_configurations'):
            return self.env.ref("xe_exam_management.report_cbc_marksheetline").report_action(self)
        if self.env.user.has_group('xe_exam_management.group_subject_rubrics_configuration'):
            return self.env.ref("xe_exam_management.report_cbc_session_wise_marksheetline").report_action(self)

    def button_cbc_combine_marksheet_line(self):
        if self.env.user.has_group('xe_exam_management.group_rubrics_configurations'):
            return self.env.ref("xe_exam_management.report_cbc_combine_marksheetline").report_action(self)
        if self.env.user.has_group('xe_exam_management.group_subject_rubrics_configuration'):
            return self.env.ref("xe_exam_management.report_cbc_session_wise_combine_marksheetline").report_action(self)

    def button_marksheet_line(self):
        return self.env.ref("xe_exam_management.report_marksheetline").report_action(
            self
        )

    def button_combine_marksheet_line(self):
        return self.env.ref(
            "xe_exam_management.report_combine_marksheetline"
        ).report_action(self)
