# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models, fields


class StudentAttendanceRegister(models.Model):
    _name = "xe.attendance.register"
    _inherit = ["mail.thread"]
    _description = "Attendance Register"

    name = fields.Char("Attendance Register", tracking=True)
    code = fields.Char(tracking=True)
    course_id = fields.Many2one("xe.course", string="Class", tracking=True)
    batch_id = fields.Many2one("xe.batch", string="Batch", tracking=True)
    class_room_id = fields.Many2one("xe.classroom", string="Classroom", tracking=True)
    subject_id = fields.Many2one("xe.subject", string="Subject", tracking=True)
    company_id = fields.Many2one(
        "res.company", "School", default=lambda self: self.env.user.company_id.id
    )
    allowed_teachers_ids = fields.Many2many("hr.employee", "register_id", "employee_id")
