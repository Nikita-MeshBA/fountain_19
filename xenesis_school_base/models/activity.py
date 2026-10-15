from odoo import fields, models


class Activity(models.Model):
    _name = "xe.activity"
    _inherit = ["mail.thread"]
    _description = "Activity"
    _rec_name = "student_id"

    student_id = fields.Many2one("xe.student", required=True)
    teacher_id = fields.Many2one("hr.employee", string="Staff")
    type_id = fields.Many2one("xe.activity.type", string="Activity Type", required=True)
    description = fields.Text()
    date = fields.Date(default=fields.Date.today(), required=True)
