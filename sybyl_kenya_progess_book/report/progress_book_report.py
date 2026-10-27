# -*- coding: utf-8 -*-
import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import date


class ReportProgressBook(models.AbstractModel):
    _name = "report.sybyl_kenya_progess_book.report_progress_book"
    _description = "Progress Book Report"

    def _get_report_details(self, course, classroom):
        course_id = self.env["xe.course"].search([("id", "=", int(course))])
        classroom_id = self.env["xe.classroom"].search([("id", "=", int(classroom))])
        subject_ids = self.env["xe.subject"].search(
            [("course_ids", "in", [int(course)])]
        )
        progress_book_ids = self.env["xe.progress.book"].search(
            [
                ("course_id", "=", course_id.id),
                ("classroom_id", "=", classroom_id.id),
                ("state", "=", "validate"),
            ]
        )

        datas = dict()
        for progress_book_id in progress_book_ids:
            pass

    @api.model
    def _get_report_values(self, docids, data=None):
        data = self._get_report_details(data["course_id"], data["classroom_id"])
        # return {
        #     'doc_ids': self.ids,
        #     'doc_model': model,
        #     'data': data['form'],
        #     'date_from': date_from,
        #     'date': date,
        #     'date_to': date_to,
        #     'variant_value': variant_value,
        #     'variant_header': variant_header,
        #     'docs': docs,
        #     'time': time,
        #     'get_details': final_result,
        # }
