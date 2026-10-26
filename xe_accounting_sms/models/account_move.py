from odoo.exceptions import UserError

from odoo import models, _


class InvoiceSms(models.Model):
    _inherit = "account.move"

    def action_post(self):
        result = super(InvoiceSms, self).action_post()
        if self.move_type == "out_invoice":
            sms_alert_rec = self.env["xe.send.sms.config"].search(
                [("active", "=", True), ("company_id", "=", self.company_id.id)]
            )
            default_invoice_validate = sms_alert_rec.is_invoice_validate
            if default_invoice_validate:
                template = sms_alert_rec.invoice_validate_tmpl_id
                send_sms_template = self.env["send.sms.template"]
                for res in self:
                    send_sms_template.send_sms(template.id, res.id)
        return result


class AccountPayments(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        """draft -> posted"""
        result = super(AccountPayments, self).action_post()
        for rec in self:
            if rec.payment_type == "inbound":
                sms_alert_rec = self.env["xe.send.sms.config"].search(
                    [("active", "=", True), ("company_id", "=", self.company_id.id)]
                )
                default_invoice_validate = sms_alert_rec.is_payment
                if default_invoice_validate:
                    template = sms_alert_rec.payment_tmpl_id
                    send_sms_template = self.env["send.sms.template"]
                    for res in self:
                        send_sms_template.send_sms(template.id, res.id)
        return result
