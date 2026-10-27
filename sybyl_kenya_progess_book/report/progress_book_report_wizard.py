# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class XeProgressBookReportWizard(models.TransientModel):
    _name = "xe.progress.book.report.wizard"
    _description = "Progress Book Report Wizard"

    course_id = fields.Many2one("xe.course")
    classroom_id = fields.Many2one("xe.classroom")

    @api.onchange("course_id")
    def _onchange_course_id(self):
        if self.course_id:
            self.classroom_id = False
            classroom_ids = self.env["xe.classroom"].search(
                [("course_id", "=", self.course_id.id)]
            )
            return {"domain": {"classroom_id": [("id", "in", classroom_ids.ids)]}}

    def print_pdf_report(self):
        data = {"course_id": self.course_id.id, "classroom_id": self.classroom_id.id}
        return self.env.ref(
            "sybyl_kenya_progess_book.action_report_progress_book"
        ).report_action(self, data=data)
