from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class SendSMSDiscipline(models.TransientModel):
    _name = "send.sms.discipline"

    def _get_active_discipline_records(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    discipline_records_ids = fields.Many2many(
        "xe.discipline.records",
        string="Discipline Records",
        default=_get_active_discipline_records,
    )
    sms_template_id = fields.Many2one(
        "send.sms.template", string="Send SMS Template", required=True
    )
    template_body = fields.Text("Body", translate=True, help="Plain text of message")

    @api.onchange("sms_template_id")
    def _set_template_body(self):
        if self.sms_template_id:
            self.template_body = False
            self.template_body = self.sms_template_id.template_body

    def action_send_sms(self):
        sms_alert_rec = self.env["xe.send.sms.config"].search([("active", "=", True)])
        default_visitor_pass_manual = sms_alert_rec.is_manual_sms

        if default_visitor_pass_manual:
            for record in self.discipline_records_ids:
                message_to = record.student_id.parent_ids.mapped("mobile")
                send_sms_template = self.env["send.sms.template"]
                sms_rendered_content = send_sms_template.render_template(
                    self.template_body, "xe.discipline.records", record.id
                )
                rendered_msg_to = send_sms_template.render_template(
                    message_to, "xe.discipline.records", record.id
                )
                gateway_model = self.env["sms.gateway.config"].search(
                    [("active", "=", True)], limit=1
                )
                if (
                    "is_mtech_sms" in self.env["sms.gateway.config"]._fields
                    and gateway_model.is_mtech_sms
                ):
                    template_id = (
                        self.sms_template_id.id if self.sms_template_id else False
                    )
                    active_model = self.env.context.get("active_model")
                    gateway_model.mtech_send_sms(
                        message_to,
                        sms_rendered_content,
                        active_model,
                        False,
                        template_id,
                    )
                else:
                    gateway_model.send_sms(message_to, sms_rendered_content)
        else:
            raise UserError(_("Sorry you cant send manual sms !!"))
