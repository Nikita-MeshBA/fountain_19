from odoo import fields, models


class ActivityType(models.Model):
    _name = "xe.activity.type"
    _inherit = ["mail.thread"]
    _description = "Activity Type"

    name = fields.Char(required=True)
