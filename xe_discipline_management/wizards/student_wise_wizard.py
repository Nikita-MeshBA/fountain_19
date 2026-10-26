# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StudentWise(models.TransientModel):
    _name = "student.wise"
    _description = "Student Wise"

    student_id = fields.Many2one("xe.student", "Student", required=True)
    from_date = fields.Date(required=True, default=lambda self: fields.Date.today())
    to_date = fields.Date(required=True, default=lambda self: fields.Date.today())

    @api.constrains("from_date", "to_date")
    def check_dates(self):
        for record in self:
            from_date = fields.Date.from_string(record.from_date)
            to_date = fields.Date.from_string(record.to_date)
            if to_date < from_date:
                raise ValidationError(_("To Date cannot be set before From Date."))

    def print_report(self):
        data = self.read(["student_id", "from_date", "to_date"])[0]
        return self.env.ref(
            "xe_discipline_management.action_report_student_wise"
        ).report_action(self, data=data)
