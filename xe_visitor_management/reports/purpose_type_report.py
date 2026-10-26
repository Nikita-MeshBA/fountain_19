# -*- coding: utf-8 -*-
import time

from odoo import models, api

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PurposeTypeWizard(models.TransientModel):
    _name = "purpose.type.wizard"

    purpose_type_id = fields.Many2one("purpose.type", "Purpose Type")
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
        """Call when button 'Get Report' clicked."""
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "purpose_type_id": self.purpose_type_id.id,
                "purpose_type_name": self.purpose_type_id.name,
                "date_start": self.from_date,
                "date_end": self.to_date,
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref("xe_visitor_management.purpose_type_report").report_action(
            self, data=data
        )


class PurposeTypeReportWise(models.AbstractModel):
    _name = "report.xe_visitor_management.report_purpose_type"
    _description = "Purpose Type Wise"

    def get_data(self, data):
        if data:
            return data

    def get_object(self, data):
        purpose_type_id = data["form"]["purpose_type_id"]
        from_date = data["form"]["date_start"]
        to_date = data["form"]["date_end"]

        type_search = self.env["visitor.pass"].search(
            [
                ("purpose_type_id", "=", purpose_type_id),
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
