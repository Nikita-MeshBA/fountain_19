from odoo import models, fields, api


class AssignmentType(models.Model):
    _name = "xe.assignment.type"
    _inherit = ["mail.thread"]
    _description = "Assignment Types"

    name = fields.Char("Assignment Type")
    code = fields.Char()
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )


class ResCompany(models.Model):
    _inherit = "res.company"

    station_code = fields.Char()


class StudentProfile(models.Model):
    _inherit = "xe.student"

    company_id = fields.Many2one("res.company")
    station_code = fields.Char(related="company_id.station_code")
