# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class XeExamRoom(models.Model):
    _name = "xe.exam.room"
    _description = "Exam Room"

    name = fields.Char(size=256, required=True)
    classroom_id = fields.Many2one("xe.classroom", required=True)
    capacity = fields.Integer(required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.constrains("capacity")
    def check_capacity(self):
        if self.capacity < 0:
            raise ValidationError(_("Enter proper Capacity"))
        elif self.capacity > self.classroom_id.capacity:
            raise ValidationError(_("Capacity over Classroom capacity!"))

    @api.onchange("classroom_id")
    def onchange_classroom(self):
        self.capacity = self.classroom_id.capacity
