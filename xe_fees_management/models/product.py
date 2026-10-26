from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_fee = fields.Boolean(string="Fee", default=True)


class Products(models.Model):
    _inherit = "product.product"

    fee_receipt_id = fields.Many2one("fee.receipt", "Fees Receipt")
    is_fee_product = fields.Boolean("Fees Product")
    is_opening_blns = fields.Boolean(default=True)
