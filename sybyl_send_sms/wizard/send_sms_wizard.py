from odoo import models, fields, _


class SendSMSWizard(models.TransientModel):
    _name = "send.sms.wizard"

    def _get_active_invoices(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    invoice_ids = fields.Many2many(
        "account.move", string="Invoices", default=_get_active_invoices
    )

    def action_send_sms(self):
        for invoice in self.invoice_ids:
            if invoice.state == "posted":
                template = self.env.ref(
                    "send_sms_invoice.send_sms_template_data_invoice_validate"
                )
                self.env["send.sms.template"].send_sms(template.id, invoice.id)
                invoice.sent_sms = True
                invoice.message_post(body=_("Sent Message"))
