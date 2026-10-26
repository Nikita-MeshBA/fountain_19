from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SendSMSVisitor(models.TransientModel):
    _name = "send.sms.visitor"

    def _get_active_visitorpass(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    visitor_pass_ids = fields.Many2many(
        "visitor.pass",
        string="Selected Visitor Records",
        default=_get_active_visitorpass,
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
            for record in self.visitor_pass_ids:
                send_sms_template = self.env["send.sms.template"]
                sms_rendered_content = send_sms_template.render_template(
                    self.template_body, "visitor.pass", record.id
                )
                message_to = record.phone
                rendered_msg_to = send_sms_template.render_template(
                    message_to, "visitor.pass", record.id
                )
                gateway_model = self.env["sms.gateway.config"].search(
                    [("active", "=", True)], limit=1
                )
                if gateway_model:
                    gateway_model.send_sms(rendered_msg_to, sms_rendered_content)
        else:
            raise UserError(_("Sorry you cant send manual sms !!"))
