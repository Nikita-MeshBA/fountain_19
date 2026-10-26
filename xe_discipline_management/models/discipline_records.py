# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DisciplineRecords(models.Model):
    _name = "xe.discipline.records"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Discipline Records"

    name = fields.Char(tracking=True)
    student_id = fields.Many2one("xe.student", tracking=True)
    discipline_date = fields.Date("Date", default=fields.Date.today(), tracking=True)
    course_id = fields.Many2one("xe.course", "Course", tracking=True)
    misbehave_type = fields.Selection(
        [("major", "Major"), ("minor", "Minor")],
        string="Misbehaviour Type",
        tracking=True,
    )
    misbehave_categ_id = fields.Many2one(
        "xe.misbehave.category", "Misbehaviour Category", tracking=True
    )
    misbehave_sub_categ_id = fields.Many2one(
        "xe.misbehave.sub.category", string="Misbehaviour Sub Category", tracking=True
    )
    action_to_take = fields.Char("Action to be Taken", tracking=True)
    notes = fields.Text()
    meeting_time = fields.Datetime("Meeting Datetime")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("action_needed", "Action Needed"),
            ("email_sent", "Email Sent"),
            ("awaiting_letter", "Awaiting Apology Letter"),
            ("awaiting_meeting", "Awaiting Meeting"),
            ("suspended", "Suspended"),
            ("done", "Done"),
        ],
        default="draft",
        tracking=True,
    )
    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High")], tracking=True
    )
    company_id = fields.Many2one(
        "res.company",
        "School",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    create_user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    classroom_id = fields.Many2one(
        "xe.classroom", string="Classroom", ondelete="cascade"
    )

    @api.onchange("student_id")
    def _set_course(self):
        for record in self:
            if record.student_id and record.student_id.course_id:
                record.course_id = record.student_id.course_id
                record.classroom_id = record.student_id.classroom_id

    def send_email_composer(self, res_model, res_id, template, partner_ids=None):
        compose_form = self.env.ref("mail.email_compose_message_wizard_form", False)
        ctx = dict(
            default_model=res_model,
            default_res_id=res_id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_partner_ids=partner_ids,
            default_composition_mode="comment",
            misbehaviour_report_as_sent=True,
            force_email=True,
        )
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    def act_send_email(self):
        partner_ids = self.student_id.parent_ids.mapped("partner_id").ids
        email_template = self.misbehave_categ_id.email_tmpl_id
        self.state = "email_sent"
        return self.send_email_composer(
            res_model="xe.discipline.records",
            res_id=self.id,
            template=email_template,
            partner_ids=partner_ids,
        )

    def act_apology_letter(self):
        self.state = "awaiting_letter"

    def act_meeting_awaiting(self):
        self.state = "awaiting_meeting"

    def act_action_needed(self):
        self.state = "action_needed"

    def act_take_action(self):
        compose_form = self.env.ref("xe_discipline_management.take_action_form")
        return {
            "name": _("Take Action"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "xe.take.action",
            "view_id": compose_form.id,
            "target": "new",
        }

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code(
            "xe.discipline.records.seq"
        ) or _("New")
        return super(DisciplineRecords, self).create(vals)
