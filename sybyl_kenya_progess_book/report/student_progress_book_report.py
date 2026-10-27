from odoo import models, api, _


class ReportStudentProgressBook(models.AbstractModel):
    _name = "report.sybyl_kenya_progess_book.student_progress_book_report"
    _description = "Student Progress Book"

    @api.model
    def _get_report_values(self, docids, data=None):
        student_id = self.env["xe.student"].search(
            [("id", "=", int(data["student_id"]))]
        )
        academic_year_id = self.env["xe.academic.year"].search(
            [("id", "=", int(data["academic_year_id"]))]
        )
        academic_term_id = self.env["xe.academic.terms"].search(
            [("id", "=", int(data["academic_term_id"]))]
        )

        marking_ids = self.env["xe.marking"].search(
            [
                ("student_id", "=", student_id.id),
                ("student_id.current_academic_year_id", "=", academic_year_id.id),
                ("academic_term_id", "=", academic_term_id.id),
            ]
        )
        docargs = {
            "doc_model": "xe.progress.book.wizard",
            "doc_ids": marking_ids,
            "docs": student_id,
            "name": student_id.name,
            "marking_ids": marking_ids,
        }
        return docargs
