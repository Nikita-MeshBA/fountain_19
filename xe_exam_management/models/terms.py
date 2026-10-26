from odoo import models, fields


class XeBatch(models.Model):
    _inherit = "xe.term"

    t1_start_date = fields.Date("Start Date")
    t1_end_date = fields.Date("End Date")
    t2_start_date = fields.Date("Start Date")
    t2_end_date = fields.Date("End Date")
    t3_start_date = fields.Date("Start Date")
    t3_end_date = fields.Date("End Date")
    sequence = fields.Char()
