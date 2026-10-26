# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class XeMarksheetRegister(models.Model):
    _name = "xe.marksheet.register"
    _description = "Marksheet Register"
    _inherit = ["mail.thread"]

    exam_session_id = fields.Many2one("xe.exam.session", required=True, tracking=True)
    marksheet_line_ids = fields.One2many(
        "xe.marksheet.line", "marksheet_reg_id", "Marksheets"
    )
    generated_date = fields.Date(
        required=True, default=fields.Date.today(), tracking=True
    )
    # old field
    generated_by = fields.Many2one(
        "res.users", default=lambda self: self.env.uid, tracking=True
    )
    # new field
    generated_by_id = fields.Many2one(
        "res.users", default=lambda self: self.env.uid, required=True, tracking=True
    )
    state = fields.Selection(
        [("draft", "Draft"), ("validated", "Validated"), ("cancelled", "Cancelled")],
        "Status",
        default="draft",
        required=True,
        tracking=True,
    )
    total_pass = fields.Integer(compute="_compute_total_pass", tracking=True)
    total_failed = fields.Integer(compute="_compute_total_failed", tracking=True)
    name = fields.Char("Marksheet Register", size=256, required=True, tracking=True)
    result_template_id = fields.Many2one(
        "xe.result.template", required=True, tracking=True
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    course_id = fields.Many2one(
        "xe.course",
        related="exam_session_id.course_id",
        store=True,
        readonly=True,
    )
    evaluation_type = fields.Selection(
        "Exam Type",
        related="exam_session_id.course_id.evaluation_type",
        store=True,
        readonly=True,
    )
    academic_term_id = fields.Many2one(
        "xe.academic.terms",
        related="exam_session_id.academic_term_id",
        store=True,
        readonly=True,
    )

    @api.constrains("total_pass", "total_failed")
    def _check_marks(self):
        if (self.total_pass < 0.0) or (self.total_failed < 0.0):
            raise ValidationError(_("Enter proper pass or fail!"))

    @api.depends("marksheet_line_ids.status")
    def _compute_total_pass(self):
        for record in self:
            count = 0
            for marksheet in record.marksheet_line_ids:
                if marksheet.status == "pass":
                    count += 1
            record.total_pass = count

    @api.depends("marksheet_line_ids.status")
    def _compute_total_failed(self):
        for record in self:
            count = 0
            for marksheet in record.marksheet_line_ids:
                if marksheet.status == "fail":
                    count += 1
            record.total_failed = count

    def action_validate(self):
        self.state = "validated"

    def action_send_email(self):
        if self.state != "validated":
            raise ValidationError(
                _("You cannot send email, the record not in validated state")
            )
        lines = self.marksheet_line_ids
        for line in lines:
            line.action_marksheet_report_sent()

    def act_cancel(self):
        self.state = "cancelled"

    def act_draft(self):
        self.state = "draft"
