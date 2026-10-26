from odoo import fields, models


class InsuranceScheme(models.Model):
    _name = "hr.insurance.scheme"
    _description = "Insurance Scheme"

    name = fields.Char(required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    amount = fields.Monetary()
