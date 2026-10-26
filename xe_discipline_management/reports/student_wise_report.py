# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################

import time
from odoo import models, api


class StudentWiseReport(models.AbstractModel):
    _name = "report.xe_discipline_management.student_wise_report"
    _description = "Student Wise Report"

    def get_data(self, data):
        if data:
            return data

    def get_object(self, data):
        discipline_search = self.env["xe.discipline.records"].search(
            [
                ("student_id", "=", data["student_id"][0]),
                ("discipline_date", ">=", data["from_date"]),
                ("discipline_date", "<=", data["to_date"]),
            ],
            order="discipline_date asc",
        )

        lst = []
        for record in discipline_search:
            dic = {
                "date": record.discipline_date,
                "misbehaviour_type": record.misbehave_type,
                "misbehaviour_category_id": record.misbehave_categ_id.name,
                "misbehaviour_sub_category_id": record.misbehave_sub_categ_id.name,
                "misbehaviour_action": record.action_to_take,
                "state": record.state,
            }
            lst.append(dic)
        return [{"record": lst}]

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["xe.discipline.records"].browse(docids)
        docargs = {
            "doc_model": "xe.discipline.records",
            "docs": docs,
            "time": time,
            "get_object": self.get_object(data),
            "get_data": self.get_data(data),
        }
        return docargs
