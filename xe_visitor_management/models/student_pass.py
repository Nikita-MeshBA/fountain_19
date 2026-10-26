# -*- coding: utf-8 -*-
from random import randint
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StudentPass(models.Model):
    _name = "student.pass"
    _inherit = ["mail.thread"]
    _rec_name = "student_id"
    _description = "Student Pass"

    def _get_default_sent_sms(self):
        is_check_otp = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_visitor_management.otp")
        )
        if is_check_otp:
            return True
        else:
            return False

    student_id = fields.Many2one("xe.student", "Student", required=True)
    profile = fields.Binary(related="student_id.image_1920")
    course_id = fields.Many2one("xe.course", string="Class", store=True, readonly=True)
    classroom_id = fields.Many2one(
        "xe.classroom", "Classroom", store=True, readonly=True
    )
    batch_id = fields.Many2one("xe.term", string="Batch", store=True)
    application_number = fields.Char(
        related="student_id.roll_number", readonly=True, string="Admission Number"
    )
    reason = fields.Text(required=True)
    person_name = fields.Char("Picked By", size=128, required=True)
    identification_no = fields.Char("Identification Number", size=64, required=False)
    relationship = fields.Char(size=64, required=True)
    approved_by_id = fields.Many2one(
        "res.users", "Approved By", required=True, default=lambda self: self.env.user.id
    )
    approved_time = fields.Datetime(required=True, default=fields.Datetime.now)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    mobile = fields.Char()
    send_otp = fields.Char()
    stud_otp = fields.Char()
    verified = fields.Boolean(default=False)
    relationship = fields.Selection(
        [
            ("father", "Father"),
            ("mother", "Mother"),
            ("relative", "Relative"),
            ("other", "Other"),
        ]
    )
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved")], default="draft"
    )
    sent_sms = fields.Boolean("Sent SMS", default=_get_default_sent_sms)

    @api.onchange("student_id", "course_id")
    def _onchange_student_course_classroom(self):
        if self.student_id:
            class_rec = (
                self.env["xe.student"].sudo().search([("id", "=", self.student_id.id)])
            )
            self.write(
                {
                    "course_id": class_rec.course_id.id,
                    "classroom_id": class_rec.classroom_id,
                }
            )

    def action_approved(self):
        for record in self:
            if record.stud_otp == record.send_otp:
                record.state = "approved"
            else:
                raise UserError(_("Please Enter Valid OTP"))

    def action_draft(self):
        for record in self:
            record.state = "draft"

    def sent_otp(self):
        template = self.env.ref("xe_visitor_management.send_otp_template")
        for res in self:
            n = 6
            range_start = 10 ** (n - 1)
            range_end = (10**n) - 1
            random_num = randint(range_start, range_end)
            self.stud_otp = random_num

            send_sms_template = self.env["send.sms.template"]
            template = send_sms_template.browse(int(template))
            if not template.active:
                return True

            rendered_msg_to = self.mobile.replace(" ", "")
            sms_rendered_content = send_sms_template.render_template(
                template.template_body, template.model_id.model, res.id
            )

            gateway_model = template.sms_account_gateway
            if gateway_model:
                gateway_model.send_sms(
                    rendered_msg_to,
                    sms_rendered_content,
                    template.model_id.model,
                    res.id,
                    template,
                )
            else:
                raise UserError(_("Gateway not defined in SMS Template"))

            res.sent_sms = True
