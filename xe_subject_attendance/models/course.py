from odoo import models, fields, api


class Course(models.Model):
    _inherit = "xe.course"

    is_attendance_subject_wise = fields.Boolean("Subject Wise Attendance")
    max_subject_registration = fields.Integer()
