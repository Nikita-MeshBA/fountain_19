from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # old field
    current_academic_year = fields.Many2one(
        "xe.academic.year"
    )
    # new field
    current_academic_year_id = fields.Many2one(
        "xe.academic.year"
    )
    is_sequence = fields.Boolean()
    mpesa_paybill = fields.Text()
    account = fields.Char()
    signature = fields.Binary()
