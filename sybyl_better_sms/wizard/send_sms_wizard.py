from odoo import api, models, fields
from odoo.exceptions import UserError


class SendSMSWizardInherit(models.TransientModel):
    _inherit = "send.sms.wizard"

    def action_send_sms(self):
        sms_alert_rec = self.env["xe.send.sms.config"].search([("active", "=", True)])
        default_invoice_manual = sms_alert_rec.is_manual_sms
        if default_invoice_manual:
            for invoice in self.invoice_ids:
                send_sms_template = self.env["send.sms.template"]
                sms_rendered_content = send_sms_template.render_template(
                    self.template_body, "account.move", invoice.id
                )
                message_to = invoice.partner_id.get_mobile_numbers()
                rendered_msg_to = send_sms_template.render_template(
                    message_to, "account.move", invoice.id
                )
                gateway_model_id = self.sms_account_gateway_id
                if gateway_model_id:
                    if gateway_model_id.is_better_sms:
                        sms_to = []
                        if "," in message_to:
                            sms_to = list(message_to.split(","))
                        else:
                            sms_to = [message_to]
                        template_id = (
                            self.sms_template_id.id if self.sms_template_id else False
                        )
                        active_model = self.env.context.get("active_model")
                        gateway_model_id.better_send_sms(
                            sms_rendered_content,
                            sms_to
                        )
                    else:
                        gateway_model_id.send_sms(rendered_msg_to, sms_rendered_content)
        else:
            raise UserError(_("Sorry you cant send manual sms !!"))
