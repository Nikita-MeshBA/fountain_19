from odoo.exceptions import UserError
from odoo import api, models, fields, _


class SendSMSWizard(models.TransientModel):
    _name = "send.sms.wizard"

    def _default_gateway_account(self):
        account_id = (
            self.env["sms.gateway.config"].search([("active", "=", True)], limit=1).id
        )
        return account_id

    def _get_active_invoices(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    invoice_ids = fields.Many2many(
        "account.move", string="Invoices", default=_get_active_invoices
    )
    sms_template_id = fields.Many2one("send.sms.template", string="Send SMS Template")
    template_body = fields.Text("Body", translate=True, help="Plain text of message")
    sms_account_gateway_id = fields.Many2one(
        "sms.gateway.config",
        string="Account",
        default=_default_gateway_account,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.onchange("sms_template_id")
    def _set_template_body(self):
        if self.sms_template_id:
            self.template_body = False
            self.template_body = self.sms_template_id.template_body

    def action_send_sms(self):
        sms_alert_rec = self.env["xe.send.sms.config"].search([("active", "=", True), ("company_id", "=", self.company_id.id)])
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
                gateway_model = self.sms_account_gateway_id
                if gateway_model:
                    gateway_model.send_sms(rendered_msg_to, sms_rendered_content)
        else:
            raise UserError(_("Sorry you cant send manual sms !!"))
