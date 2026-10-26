from odoo import api, fields, models


class SaleSmsSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_invoice_paid = fields.Boolean("Send SMS on invoice paid")
    is_invoice_validate = fields.Boolean("Send SMS on invoice validate")
    is_inv_validate_manual = fields.Boolean("Send SMS Manually for invoice")

    @api.model
    def get_values(self):
        res = super(SaleSmsSettings, self).get_values()
        get_param = self.env["ir.config_parameter"].sudo().get_param

        res.update(is_invoice_paid=get_param("send_sms_invoice.is_invoice_paid"))
        res.update(
            is_invoice_validate=get_param("send_sms_invoice.is_invoice_validate")
        )
        res.update(
            is_inv_validate_manual=get_param("send_sms_invoice.is_inv_validate_manual")
        )
        return res

    def set_values(self):
        super(SaleSmsSettings, self).set_values()
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("send_sms_invoice.is_invoice_paid", self.is_invoice_paid)
        set_param("send_sms_invoice.is_invoice_validate", self.is_invoice_validate)
        set_param(
            "send_sms_invoice.is_inv_validate_manual", self.is_inv_validate_manual
        )
