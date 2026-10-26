
from odoo import models, fields, _


class AccountInvoice(models.Model):
    _inherit = "account.move"
    
    reg_payment = fields.Float("Register Payment")