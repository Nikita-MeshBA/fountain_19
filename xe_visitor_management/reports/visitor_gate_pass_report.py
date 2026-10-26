# -*- coding: utf-8 -*-
import time
from odoo import models, api


class VisitorGatePassReport(models.AbstractModel):
    _name = "report.xe_visitor_management.visitor_visitor_pass_report"
    _description = "Visitor Gatee Pass Type"

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env["visitor.pass"].browse(docids)
        docargs = {
            "doc_model": "visitor.pass",
            "docs": docs,
            "time": time,
        }
        return docargs
