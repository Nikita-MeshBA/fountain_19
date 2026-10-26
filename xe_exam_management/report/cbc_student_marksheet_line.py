# -*- coding: utf-8 -*
import time
from datetime import datetime
from odoo import models, api, fields


class ReportCBCMarksheetLineReport(models.AbstractModel):
    _name = "report.xe_exam_management.cbc_mark_line_rep"
    _description = "Exam Management CBC Marksheet Line Report"

    def get_details(self, marksheet_line_obj):
        student = marksheet_line_obj.student_id and marksheet_line_obj.student_id.name
        exam_code = (
            marksheet_line_obj.marksheet_reg_id.exam_session_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.exam_code
        )
        course = (
            marksheet_line_obj.marksheet_reg_id.exam_session_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.course_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.course_id.name
        )
        exam_session = (
            marksheet_line_obj.marksheet_reg_id.exam_session_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.name
        )
        date1 = marksheet_line_obj.marksheet_reg_id.generated_date
        date = str(date1.month) + " / " + str(date1.year)
        marks_total = [
            x.exam_id.total_marks for x in marksheet_line_obj.result_line_ids
        ]
        total_marks = sum(marks_total)
        total_obtained_marks = marksheet_line_obj.total_marks or 0
        total_percentage = marksheet_line_obj.percentage
        total_status = dict(
            marksheet_line_obj.fields_get(allfields=["status"])["status"]["selection"]
        )[marksheet_line_obj.status]
        total_grade = marksheet_line_obj.grade or ""
        evaluation_type = marksheet_line_obj.student_id.course_id.evaluation_type
        term = marksheet_line_obj.exam_session_id.exam_type_id.name
        academic_term = (
            marksheet_line_obj.exam_session_id.academic_term_id.name
            if marksheet_line_obj.exam_session_id.academic_term_id
            else ""
        )

        term_end_date = (
            marksheet_line_obj.academic_term_id.end_date
            and datetime.strftime(
                marksheet_line_obj.academic_term_id.end_date, "%d/%m/%y"
            )
        )
        opening_next_term_date = (
            marksheet_line_obj.academic_term_id.next_term_open_date
            and datetime.strftime(
                marksheet_line_obj.academic_term_id.next_term_open_date,
                "%d/%m/%y",
            )
            or ""
        )

        line = marksheet_line_obj
        general_comment = line.head_master_comment
        extra_comment = line.extra_curr_comment
        head_teacher_comment = line.head_teacher_comment

        teacher_name = (
            line.classroom_id.teacher_id and line.classroom_id.teacher_id.name or ""
        )
        teacher_signature = (
            line.classroom_id and line.classroom_id.teacher_signature_html or ""
        )

        head_teacher_name = (
            line.exam_session_id.course_id
            and line.exam_session_id.course_id.head_teacher_id
            and line.exam_session_id.course_id.head_teacher_id.name
            or ""
        )
        head_teacher_signature = (
            line.exam_session_id.course_id
            and line.exam_session_id.course_id.head_teacher_signature
        )

        exam_details = []
        rubric_ee = rubric_me = rubric_ae = rubric_be = ""
        for rec in marksheet_line_obj.result_line_ids:
            if rec.exam_id.subject_id.show_on_report_card:
                rubric = self.find_rubrics(rec.marks)
                if rubric == "EE":
                    rubric_ee = rubric
                elif rubric == "ME":
                    rubric_me = rubric
                elif rubric == "AE":
                    rubric_ae = rubric
                elif rubric == "BE":
                    rubric_be = rubric
                values = {
                    "exam": rec.exam_id.subject_id and rec.exam_id.subject_id.name,
                    "sequence": rec.exam_id.subject_id
                    and rec.exam_id.subject_id.sequence,
                    "exam_type": rec.exam_id.session_id.exam_type_id.name,
                    "total_marks": rec.exam_id.total_marks,
                    "minimum_marks": rec.exam_id.min_marks,
                    "obtained_marks": rec.marks,
                    "grade": rec.grade,
                    "rubric_ee": rubric_ee,
                    "rubric_me": rubric_me,
                    "rubric_ae": rubric_ae,
                    "rubric_be": rubric_be,
                }
                rubric_dict = self.get_rubrics(rec.marks)
                values.update(rubric_dict)
                rubric_ee = rubric_me = rubric_ae = rubric_be = ""
                exam_details.append(values)

        rubrics_range_ee = rubrics_range_me = rubrics_range_ae = rubrics_range_be = ""
        rubrics = self.env["xe.rubrics.configuration"].search(
            [
                ("company_id", "=", marksheet_line_obj.company_id.id),
                ("exam_session_id", "=", False),
                ("subject_id", "=", False),
            ]
        )
        for i in rubrics:
            if i.code == "EE":
                rubrics_range_ee = str(i.min_per) + "-" + str(i.max_per)
            if i.code == "ME":
                rubrics_range_me = str(i.min_per) + "-" + str(i.max_per)
            if i.code == "AE":
                rubrics_range_ae = str(i.min_per) + "-" + str(i.max_per)
            if i.code == "BE":
                rubrics_range_be = str(i.min_per) + "-" + str(i.max_per)

        show_marks = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("xe_exam_management.show_marks_in_cbc_report")
        )
        final_vals = {
            "exam_details": self.set_subject_sequence(exam_details),
            "rubrics_range_ee": rubrics_range_ee,
            "rubrics_range_me": rubrics_range_me,
            "rubrics_range_ae": rubrics_range_ae,
            "rubrics_range_be": rubrics_range_be,
            "student": student,
            "exam_code": exam_code,
            "course": course,
            "exam_session": exam_session,
            "date": date,
            "term": term,
            "academic_term": academic_term,
            "total_marks": total_marks,
            "total_obtained_marks": total_obtained_marks,
            "total_percentage": total_percentage,
            "total_status": total_status,
            "total_grade": total_grade,
            "evaluation_type": evaluation_type,
            "comments": rec.comments,
            "general_comment": general_comment,
            "extra_comment": extra_comment,
            "teacher_name": teacher_name,
            "teacher_signature": teacher_signature,
            "head_teacher_name": head_teacher_name,
            "head_teacher_signature": head_teacher_signature,
            "head_teacher_comment": head_teacher_comment,
            "current_date": fields.Datetime.now(),
            "head_master_comment": marksheet_line_obj.head_master_comment or "",
            "rubrics_details": rubrics,
            "show_marks": True if show_marks else False,
            "admission_no": marksheet_line_obj.student_id.roll_number,
            "academic_year_id": marksheet_line_obj.academic_year_id
            and marksheet_line_obj.academic_year_id.name
            or "",
            "classroom_name": marksheet_line_obj.classroom_id
            and marksheet_line_obj.classroom_id.name
            or "",
            "classroom_teacher_name": marksheet_line_obj.student_id.classroom_id.teacher_id
            and marksheet_line_obj.student_id.classroom_id.teacher_id.name
            or "",
            "class_teacher_name": marksheet_line_obj.student_id.course_id
            and marksheet_line_obj.student_id.course_id.head_teacher_id
            and marksheet_line_obj.student_id.course_id.head_teacher_id.name
            or "",
            "term_end_date": term_end_date,
            "opening_next_term_date": opening_next_term_date,
        }
        return final_vals

    def get_rubrics(self, average):
        rubric = {}
        rubrics = (
            self.env["xe.rubrics.configuration"].search(
                [("min_per", "<=", average), ("max_per", ">=", average)]
            )
            and self.env["xe.rubrics.configuration"].search(
                [("min_per", "<=", average), ("max_per", ">=", average)]
            )[0]
            or False
        )

        if rubrics:
            rubric["%s" % rubrics.name] = True
        return rubric

    def find_rubrics(self, average):
        rubric = ""
        rubrics = (
            self.env["xe.rubrics.configuration"].search(
                [("min_per", "<=", average), ("max_per", ">=", average)]
            )
            and self.env["xe.rubrics.configuration"].search(
                [("min_per", "<=", average), ("max_per", ">=", average)]
            )[0]
            or False
        )

        if rubrics:
            rubric = rubrics.code
        return rubric

    @api.model
    def _get_report_values(self, docids, data=None):
        marksheet_line_id = docids
        if data and data.get("form") and data["form"]["marksheet_line_id"]:
            marksheet_line_id = data["form"]["marksheet_line_id"]
        marksheet_line_obj = self.env["xe.marksheet.line"].browse(marksheet_line_id)
        get_data = self.get_details(marksheet_line_obj)
        docargs = {
            "doc_model": "xe.marksheet.line",
            "docs": marksheet_line_obj,
            "time": time,
            "get_lines": get_data,
        }
        return docargs

    def set_subject_sequence(self, exam_details):
        new_exam_details = sorted(exam_details, key=lambda i: (i["sequence"]))
        return new_exam_details
