# -*- coding: utf-8 -*-

from odoo import models, fields


class XeExamType(models.Model):
    _name = "xe.exam.type"
    _description = "Exam Type"

    name = fields.Char(size=256, required=True)
    code = fields.Char(size=16, required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        (
            "unique_exam_type_code",
            "unique(code)",
            "Code should be unique per exam type!",
        )
    ]
