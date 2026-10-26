from odoo import fields, models


class SmsMobileConfig(models.Model):
    _name = "mobile.property.config"
    _description = "Mobile Property Config"

    name = fields.Char("Property name of Mobile")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)


class SmsMessageConfig(models.Model):
    _name = "message.property.config"
    _description = "Message Property Config"

    name = fields.Char("Property name of Mobile")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
