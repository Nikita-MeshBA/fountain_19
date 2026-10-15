from odoo import models, fields


class StudentClass(models.Model):
    _name = "xe.student.course"
    _description = "Student Class Details"

    student_id = fields.Many2one("xe.student", ondelete="cascade")
    course_id = fields.Many2one("xe.course", string="Class")
    term_id = fields.Many2one("xe.term")
    roll_number = fields.Char(related="student_id.roll_number")
    stream_id = fields.Many2one("xe.stream")
    classroom_id = fields.Many2one("xe.classroom", ondelete="cascade")
