from odoo import fields, models


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    is_interview_fee = fields.Boolean()
