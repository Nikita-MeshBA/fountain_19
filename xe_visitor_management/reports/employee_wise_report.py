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


class EmployeeWise(models.TransientModel):
    _name = "employee.wise"
    _description = "Employee Type Wise"

    meeting_with_id = fields.Many2one("hr.employee", "Employee")
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
        data = self.read(["meeting_with_id", "from_date", "to_date"])[0]
        return self.env.ref("xe_visitor_management.empoyee_wise_report").report_action(
            self, data=data
        )


class EmployeeWiseReport(models.AbstractModel):
    _name = "report.xe_visitor_management.report_empoyee_wise"

    def get_data(self, data):
        if data:
            return data

    def get_object(self, data):
        meeting_with_id = data["meeting_with_id"][0]
        from_date = data["from_date"]
        to_date = data["to_date"]
        type_search = self.env["visitor.pass"].search(
            [
                ("meeting_with_id", "=", meeting_with_id),
                ("visitor_in_time", ">=", from_date),
                ("visitor_in_time", "<=", to_date),
            ],
            order="visitor_in_time asc",
        )
        lst = []
        dic = {}
        for record in type_search:
            dic = {
                "pass_number": record.pass_number,
                "name": record.name,
                "approved_by_id": record.approved_by_id.name,
                "duty_officer_name_id": record.duty_officer_name_id.name,
                "visitor_in_time": record.visitor_in_time,
                "visitor_out_time": record.visitor_out_time,
                "state": record.state,
            }
            lst.append(dic)
        return [{"record": lst}]

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["visitor.pass"].browse(docids)
        docargs = {
            "doc_model": "visitor.pass",
            "docs": docs,
            "time": time,
            "get_data": self.get_data(data),
            "get_object": self.get_object(data),
        }
        return docargs
