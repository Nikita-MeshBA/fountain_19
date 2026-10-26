from odoo import models, fields


class Course(models.Model):
    _inherit = "xe.course"

    evaluation_type = fields.Selection(
        [
            ("1-3 CBC", "CBC"),
            ("8-4-4", "8-4-4"),
            ("Kindergarten", "Kindergarten"),
            ("Playgroup", "Playgroup"),
            ("Pre Primary", "Pre Primary"),
            ("Cambridge", "Cambridge"),
        ],
        default="8-4-4",
        required=True,
    )
    head_teacher_id = fields.Many2one(
        "hr.employee", domain="[('teach_type','=','teaching')]"
    )
    head_teacher_signature = fields.Binary(string="Signature")
