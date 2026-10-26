from odoo import models, api


class ReportCBCMarksheetReport(models.AbstractModel):
    _name = "report.xe_exam_management.report_cbc_session_wise"
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
        for obj in docs:
            for marksheet_line in obj.marksheet_line:
                vals = {
                    "student_name": marksheet_line.student_id.name,
                    "course_name": marksheet_line.course_id.name,
                }
                term = obj.exam_session_id.exam_type_id.name
                academic_term = obj.exam_session_id.academic_term_id.name
                vals["term"] = term
                vals["academic_term"] = academic_term
                vals["head_teacher_comment"] = marksheet_line.head_teacher_comment
                head_teacher_name = (
                    obj.exam_session_id.course_id
                    and obj.exam_session_id.course_id.head_teacher_id
                    and obj.exam_session_id.course_id.head_teacher_id.name
                    or ""
                )
                head_teacher_signature = (
                    obj.exam_session_id.course_id
                    and obj.exam_session_id.course_id.head_teacher_signature
                )
                vals["head_teacher_name"] = head_teacher_name
                vals["head_teacher_signature"] = head_teacher_signature
                evaluation_type = marksheet_line.student_id.course_id.evaluation_type
                vals["evaluation_type"] = evaluation_type
                vals["result_line"] = []
                for line in marksheet_line.result_line_ids:
                    rubrics_code = self.get_rubrics_code(
                        line.marks, line.subject_id, obj.exam_session_id
                    )
                    line_vals = {"LEARNING AREA": line.exam_id.name}
                    if rubrics_code:
                        rubrics_name = rubrics_code.upper()
                        line_vals[rubrics_name] = True
                        vals["result_line"].append(line_vals)
                data_lines.append(vals)
        return data_lines

    # Get all the rubrics code configurations as header
    def _get_header_lines(self):
        headers = ["LEARNING AREA"]
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
        docs = self.env["xe.marksheet.register"].browse(docids)
        data = self._get_data(docs)
        header_data = self._get_header_lines()
        docargs = {
            "doc_model": "xe.marksheet.register",
            "docs": docs,
            "header_data": header_data,
            "data_line": data,
            "point_lines": self._get_points_lines(),
        }
        return docargs
