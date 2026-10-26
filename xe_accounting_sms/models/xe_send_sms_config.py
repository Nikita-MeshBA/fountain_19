# -*- coding: utf-8 -*-

from odoo.exceptions import UserError

from odoo import models, fields, api, _


class XeAccountingSms(models.Model):
    _name = "xe.send.sms.config"
    _description = "SMS Configuration for Accounting"

    name = fields.Char("", default="SMS Alert Configuration")
    active = fields.Boolean(default=True)
    is_invoice_validate = fields.Boolean("Invoice Validation")
    is_payment = fields.Boolean("Customer Payment")
    is_manual_sms = fields.Boolean("Manual SMS")
    invoice_validate_tmpl_id = fields.Many2one(
        "send.sms.template", "Template for Invoice Validation"
    )
    payment_tmpl_id = fields.Many2one("send.sms.template", "Template for Payments")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.constrains("name")
    def _check_one_active_rec(self):
        for rec in self:
            rec_count = self.env["xe.send.sms.config"].search_count(
                [("active", "=", True), ("company_id", "=", self.env.company.id)]
            )
            if rec_count > 1:
                raise UserError(_("You can set only one active record"))


class Partner(models.Model):
    _inherit = "res.partner"

    def get_mobile_numbers(self):
        mobile_numbers = []
        mobile = self.mobile or ""
        phone_code = self.country_id.phone_code or ""
        if mobile and not phone_code:
            mobile_numbers.append(mobile)
        if mobile and phone_code:
            tmp_mobile = mobile
            mobile = "+" + str(phone_code) + str(tmp_mobile)
            mobile_numbers.append(mobile)
        student = self.env["xe.student"].search([("partner_id", "=", self.id)])
        if student and student.parent_ids:
            for parent in student.parent_ids:
                mobile = parent.partner_id.mobile or ""
                phone_code = parent.partner_id.country_id.phone_code or ""
                if mobile and not phone_code:
                    mobile_numbers.append(mobile)
                if mobile and phone_code:
                    tmp_mobile = mobile
                    p_mobile = "+" + str(phone_code) + str(tmp_mobile)
                    mobile_numbers.append(p_mobile)
        mobile_nos = ",".join(mobile_numbers)
        return mobile_nos
