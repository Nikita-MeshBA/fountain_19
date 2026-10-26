from odoo import fields, models


class ClassDetails(models.Model):
    _inherit = "xe.course"

    fees_term_id = fields.Many2one("xe.fees.term")
    is_add_interview_fee = fields.Boolean("Add Interview Fee")
    interview_pdt_id = fields.Many2one("product.product", "Interview Fee Product")
