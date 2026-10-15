from odoo import fields, models


class StreameDetails(models.Model):
    _name = "xe.stream"
    _inherit = ["mail.thread"]
    _description = "Stream Details"

    name = fields.Char()
    code = fields.Char()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
