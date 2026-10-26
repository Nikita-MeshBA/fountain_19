from odoo import api, models, fields


class InvoiceSms(models.Model):
    _inherit = "account.move"

    def _get_default_sent_sms(self):
        is_inv_validate_manual = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("send_sms_invoice.is_inv_validate_manual")
        )
        if is_inv_validate_manual:
            return False
        else:
            return True

    sent_sms = fields.Boolean("Sent SMS", default=_get_default_sent_sms)

    def action_invoice_paid(self):
        result = super(InvoiceSms, self).action_invoice_paid()
        default_invoice_paid = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("send_sms_invoice.is_invoice_paid")
        )
        if default_invoice_paid:
            template = self.env.ref(
                "send_sms_invoice.send_sms_template_data_invoice_paid"
            )
            send_sms_template = self.env["send.sms.template"]
            for res in self:
                send_sms_template.send_sms(template.id, res.id)
        return result

    def action_post(self):
        result = super(InvoiceSms, self).action_post()
        default_invoice_validate = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("send_sms_invoice.default_invoice_validate")
        )
        is_inv_validate_manual = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("send_sms_invoice.is_inv_validate_manual")
        )
        if default_invoice_validate and not is_inv_validate_manual:
            template = self.env.ref(
                "send_sms_invoice.send_sms_template_data_invoice_validate"
            )
            send_sms_template = self.env["send.sms.template"]
            for res in self:
                send_sms_template.send_sms(template.id, res.id)
        return result

    def send_invoice_message(self):
        template = self.env.ref(
            "send_sms_invoice.send_sms_template_data_invoice_validate"
        )
        send_sms_template = self.env["send.sms.template"]
        for res in self:
            send_sms_template.send_sms(template.id, res.id)
            res.sent_sms = True
            res.message_post(body=_("Sent Message"))
