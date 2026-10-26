from datetime import datetime

from odoo import models, api


class ReportCBCMarksheetReport(models.AbstractModel):
    _name = "report.xe_exam_management.session_wise_mark_line"
    _description = "Exam Management CBC Marksheet Report"

    def get_rubrics_code(self, marks, subject, exam_session):
        rubrics = self.env["xe.rubrics.configuration"].search(
            [
                ("min_per", "<=", marks),
                ("max_per", ">=", marks),
                ("subject_id", "=", subject.id),
                ("exam_session_id", "=", exam_session.id),
            ],
            limit=1,
        )
        if rubrics:
            return rubrics.new_code_id.name
        else:
            return False

    def _get_data(self, docs):
        data_lines = []
        for marksheet_line in docs:
            vals = {
                "student_name": marksheet_line.student_id.name,
                "course_name": marksheet_line.course_id.name,
                "admission_number": marksheet_line.student_id.roll_number,
            }
            term = marksheet_line.marksheet_reg_id.exam_session_id.exam_type_id.name
            academic_term = (
                marksheet_line.marksheet_reg_id.exam_session_id.academic_term_id.name
            )
            vals["term"] = term
            vals["academic_term"] = academic_term
            vals["head_teacher_comment"] = marksheet_line.head_teacher_comment
            teacher_signature = (
                marksheet_line.classroom_id
                and marksheet_line.classroom_id.teacher_signature_html
                or ""
            )

            head_teacher_signature = (
                marksheet_line.exam_session_id.course_id
                and marksheet_line.exam_session_id.course_id.head_teacher_signature
            )
            head_teacher_name = (
                marksheet_line.marksheet_reg_id.exam_session_id.course_id
                and marksheet_line.marksheet_reg_id.exam_session_id.course_id.head_teacher_id
                and marksheet_line.marksheet_reg_id.exam_session_id.course_id.head_teacher_id.name
                or ""
            )
            term_end_date = marksheet_line.academic_term_id and datetime.strftime(
                marksheet_line.academic_term_id.end_date,
                "%d/%m/%y",
            )
            opening_next_term_date = (
                marksheet_line.academic_term_id.next_term_open_date
                and datetime.strftime(
                    marksheet_line.academic_term_id.next_term_open_date,
                    "%d/%m/%y",
                )
                or ""
            )
            # head_teacher_signature = (
            #     marksheet_line.marksheet_reg_id.exam_session_id.course_id
            #     and marksheet_line.marksheet_reg_id.exam_session_id.course_id.head_teacher_signature
            # )
            vals["term_end_date"] = term_end_date
            vals["opening_next_term_date"] = opening_next_term_date
            vals["head_teacher_name"] = head_teacher_name
            vals["teacher_signature"] = teacher_signature
            vals["head_teacher_signature"] = head_teacher_signature
            evaluation_type = marksheet_line.student_id.course_id.evaluation_type
            vals["evaluation_type"] = evaluation_type
            vals["result_line"] = []
            vals["register_generated_date"] = datetime.strftime(
                marksheet_line.marksheet_reg_id.generated_date, "%d/%m/%y"
            )
            vals["head_master_comment"] = marksheet_line.head_master_comment or ""
            params = self.env["res.config.settings"].sudo().get_values()
            is_exam_session_wise_rubics = params.get(
                "group_subject_rubrics_configuration"
            )
            if is_exam_session_wise_rubics == "True":
                vals["is_exam_session_wise_rubics"] = True
            else:
                vals["is_exam_session_wise_rubics"] = False
            for line in marksheet_line.result_line_ids:
                rubrics_code = self.get_rubrics_code(
                    line.marks,
                    line.subject_id,
                    marksheet_line.marksheet_reg_id.exam_session_id,
                )
                line_vals = {
                    "LEARNING AREA": line.subject_id.name,
                    "sequence": line.subject_id.sequence,
                }

                show_marks = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("xe_exam_management.show_marks_in_cbc_report")
                )
                if show_marks:
                    line_vals["MARKS"] = line.marks
                if rubrics_code:
                    rubrics_name = rubrics_code.upper()
                    line_vals[rubrics_name] = True
                    vals["result_line"].append(line_vals)
            data_lines.append(vals)
        data_lines[0]["result_line"] = self.set_subject_sequence(
            data_lines[0]["result_line"]
        )
        return data_lines

    def _get_header_lines(self):
        headers = ["LEARNING AREA"]

        show_marks = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_exam_management.show_marks_in_cbc_report")
        )
        if show_marks:
            headers.append("MARKS")

        rubrics_code = self.env["xe.rubrics.code"].search([], order="points DESC")
        for code in rubrics_code:
            headers.append(code.name.upper())
        return headers

    def _get_points_lines(self):
        rubrics_code = self.env["xe.rubrics.code"].search([], order="points DESC")
        vals_list = {}
        for code in rubrics_code:
            vals_list[code.name] = code.points
        return vals_list

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["xe.marksheet.line"].browse(docids)
        data = self._get_data(docs)
        header_data = self._get_header_lines()
        docargs = {
            "doc_model": "xe.marksheet.line",
            "docs": docs,
            "data_line": data,
            "header_data": header_data,
            "point_lines": self._get_points_lines(),
            "company": docs.company_id
        }
        return docargs

    def set_subject_sequence(self, exam_details):
        new_exam_details = sorted(exam_details, key=lambda i: (i["sequence"]))
        return new_exam_details
