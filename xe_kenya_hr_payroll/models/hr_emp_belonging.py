from odoo import fields, models


class EmployeeBelongings(models.Model):
    _name = "hr.employee.belonging"
    _description = "HR Employee Belonging"

    name = fields.Char("Description")
    code = fields.Char()
