# -*- coding: utf-8 -*-

import time

from odoo import models, api


class ReportMarksheetReport(models.AbstractModel):
    _name = "report.xe_exam_management.report_marksheet_report"
    _description = "Exam Management Marksheet Report"

    def get_objects(self, objects):
        obj = []
        for object in objects:
            obj.extend(object)
        return obj

    def get_lines(self, obj):
        lines = []
        for line in obj.marksheet_line:
            lines.extend(line)
        return lines

    def get_date(self, date):
        date1 = date
        return str(date1.month) + " / " + str(date1.year)

    def get_total(self, marksheet_line):
        total = [x.exam_id.total_marks for x in marksheet_line.result_line_ids]
        return sum(total)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["xe.marksheet.register"].browse(docids)
        docargs = {
            "doc_model": "xe.marksheet.register",
            "docs": docs,
            "time": time,
            "get_objects": self.get_objects,
            "get_lines": self.get_lines,
            "get_date": self.get_date,
            "get_total": self.get_total,
        }
        return docargs
