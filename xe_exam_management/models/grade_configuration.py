# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class XeGradeConfiguration(models.Model):
    _name = "xe.grade.configuration"
    _description = "Grade Configuration"
    _rec_name = "result"

    min_per = fields.Integer("Minimum Percentage", required=True)
    max_per = fields.Integer("Maximum Percentage", required=True)
    result = fields.Char("Result to Display", required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    grade_category_id = fields.Many2one("xe.grade.category")

    @api.constrains("min_per", "max_per")
    def _validate_percentage(self):
        for record in self:
            if record.max_per > 100:
                raise ValidationError(_("Enter proper Percentage!"))
            if record.min_per > record.max_per:
                raise ValidationError(
                    _('"Maximum Percentage" must be greater than "Minimum Percentage"')
                )
