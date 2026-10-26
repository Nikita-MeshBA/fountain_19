from odoo import models, fields


class XeClassroom(models.Model):
    _inherit = "xe.classroom"

    teacher_id = fields.Many2one(
        "hr.employee", domain="[('teach_type','=','teaching')]"
    )
