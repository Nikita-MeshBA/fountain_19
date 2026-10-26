# -*- coding: utf-8 -*-
import time
from odoo import models, api


class StudentGatePassReport(models.AbstractModel):
    _name = "report.xe_visitor_management.student_visitor_pass_report"
    _description = "Student Gate Pass Report"

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env["student.pass"].browse(docids)
        docargs = {
            "doc_model": "student.pass",
            "docs": docs,
            "time": time,
        }
        return docargs
