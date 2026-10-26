# -*- coding: utf-8 -*-
###############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StudentPassWise(models.TransientModel):
    _name = "student.pass.wise"
    _description = "Student Pass Wise"

    from_date = fields.Date(default=lambda self: fields.Date.today())
    to_date = fields.Date(default=lambda self: fields.Date.today())

    @api.constrains("from_date", "to_date")
    def check_dates(self):
        for record in self:
            from_date = fields.Date.from_string(record.from_date)
            to_date = fields.Date.from_string(record.to_date)
            if to_date < from_date:
                raise ValidationError(_("To Date cannot be set before From Date."))

    def print_report(self):
        data = self.read(["from_date", "to_date"])[0]
        return self.env.ref(
            "xe_visitor_management.student_pass_wise_report"
        ).report_action(self, data=data)


class StudentPassWiseReport(models.AbstractModel):
    _name = "report.xe_visitor_management.report_student_pass_wise"

    def get_data(self, data):
        if data:
            return data

    def get_object(self, data):
        pass_search = self.env["student.pass"].search(
            [
                ("approved_time", ">=", data["from_date"]),
                ("approved_time", "<=", data["to_date"]),
            ],
            order="approved_time asc",
        )
        lst = []
        dic = {}
        for record in pass_search:
            dic = {
                "application_number": record.application_number,
                "student_id": record.student_id.name,
                "course_id": record.course_id.name,
                "batch_id": record.batch_id.name,
                "approved_by_id": record.approved_by_id.name,
                "approved_time": record.approved_time,
                "reason": record.reason,
            }
            lst.append(dic)
        return [{"record": lst}]

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["student.pass"].browse(docids)
        docargs = {
            "doc_model": "student.pass",
            "docs": docs,
            "time": time,
            "get_data": self.get_data(data),
            "get_object": self.get_object(data),
        }
        return docargs
