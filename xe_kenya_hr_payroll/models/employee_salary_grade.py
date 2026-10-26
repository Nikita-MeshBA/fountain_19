# -*- coding: utf-8 -*-

from odoo import models, fields


class EmployeeSalaryGrade(models.Model):
    _name = "hr.salary.grade"
    _description = "Salary Grade"

    def _get_company_currency(self):
        for rec in self:
            rec.currency_id = self.env.company.currency_id

    name = fields.Char("Employee Category")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        string="Currency",
        help="Utility field to express amount currency",
    )
    low_band = fields.Monetary("Minimum Band", currency_field="currency_id")
    mid_band = fields.Monetary("Intermediate Band", currency_field="currency_id")
    high_band = fields.Monetary("Maximum Band", currency_field="currency_id")
