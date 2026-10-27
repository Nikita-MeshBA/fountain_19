# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class XeProgressBookWizard(models.TransientModel):
    _name = "xe.progress.book.wizard"
    _description = "Progress Book Wizard"

    student_id = fields.Many2one("xe.student")
    academic_year_id = fields.Many2one("xe.academic.year")
    academic_term_id = fields.Many2one("xe.academic.terms")

    def generate_summary(self):
        data = {
            "student_id": self.student_id.id,
            "academic_year_id": self.academic_year_id.id,
            "academic_term_id": self.academic_term_id.id,
        }
        if not self.student_id.course_id.progress_book_pdf_format:
            raise ValidationError(
                _(
                    f"Class - %s not set progress book PDF format. {self.student_id.course_id.name}"
                )
            )
        if self.student_id.course_id.progress_book_pdf_format == "format1":
            return self.env.ref(
                "sybyl_kenya_progess_book.action_student_progress_report_format_1"
            ).report_action(self, data=data)
        if self.student_id.course_id.progress_book_pdf_format == "format2":
            return self.env.ref(
                "sybyl_kenya_progess_book.action_student_progress_report_format_2"
            ).report_action(self, data=data)
