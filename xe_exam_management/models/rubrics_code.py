from odoo import models, fields


# Used for configure rubrics code which will used during rubrics configuration bot in subject wise and generic
class XeRubricsCode(models.Model):
    _name = "xe.rubrics.code"
    _description = "Rubrics Code"
    _rec_name = "code"

    name = fields.Char()
    code = fields.Char()
    points = fields.Integer()
