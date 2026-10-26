from odoo import fields, models


class ResCountrySms(models.Model):
    _inherit = "res.country"

    sms_mobile_prefix = fields.Char(string="Mobile Prefix")
