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


class MisbehaviourTypeReport(models.AbstractModel):
    _name = "report.xe_discipline_management.misbehaviour_type_report"
    _description = "Misbehaviour Type Report"

    def get_data(self, data):
        if data:
            return data

    def get_object(self, data):
        discipline_search = self.env["xe.discipline.records"].search(
            [
                ("misbehave_type", "=", data["misbehaviour_type"]),
                ("discipline_date", ">=", data["from_date"]),
                ("discipline_date", "<=", data["to_date"]),
            ],
            order="discipline_date asc",
        )

        lst = []
        for record in discipline_search:
            dic = {
                "name": record.student_id.name,
                "misbehaviour_category_id": record.misbehave_categ_id.name,
                "misbehaviour_sub_category_id": record.misbehave_sub_categ_id.name,
                "date": record.discipline_date,
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
            "get_data": self.get_data(data),
            "get_object": self.get_object(data),
        }
        return docargs
