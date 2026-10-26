import time
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from odoo import models, api


class ReportMarksheetLineReport(models.AbstractModel):
    _name = "report.xe_exam_management.report_marksheetline_report"
    _description = "Exam Management Marksheet Line Report"

    def get_details(self, marksheet_line_obj):
        student = marksheet_line_obj.student_id and marksheet_line_obj.student_id.name
        admission_no = marksheet_line_obj.student_id.roll_number
        course_id = marksheet_line_obj.course_id.id
        classroom_name = marksheet_line_obj.student_id.classroom_id.name
        exam_code = (
            marksheet_line_obj.marksheet_reg_id.exam_session_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.exam_code
        )
        course = (
            marksheet_line_obj.marksheet_reg_id.exam_session_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.course_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.course_id.name
        )

        term_end_date = marksheet_line_obj.marksheet_reg_id.exam_session_id and datetime.strftime(
            marksheet_line_obj.marksheet_reg_id.exam_session_id.academic_term_id.end_date,
            "%d/%m/%y",
        )
        opening_next_term_date = (
            marksheet_line_obj.academic_term_id.next_term_open_date
            and datetime.strftime(
                marksheet_line_obj.academic_term_id.next_term_open_date,
                "%d/%m/%y",
            )
            or ""
        )
        teacher_signature = (
            marksheet_line_obj.student_id.classroom_id.teacher_signature_html
        )
        head_teacher_signature = (
            marksheet_line_obj.student_id.classroom_id.course_id
            and marksheet_line_obj.student_id.classroom_id.course_id.head_teacher_signature
        )

        exam_session = (
            marksheet_line_obj.marksheet_reg_id.exam_session_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.name
        )
        date1 = marksheet_line_obj.marksheet_reg_id.generated_date
        date = str(date1.month) + " / " + str(date1.year)
        total_marks = 0
        for x in marksheet_line_obj.result_line_ids:
            if x.exam_id.subject_id.is_parent:
                total_marks += x.exam_id.total_marks
        total_status = dict(
            marksheet_line_obj.fields_get(allfields=["status"])["status"]["selection"]
        )[marksheet_line_obj.status]
        total_grade = marksheet_line_obj.grade or ""
        evaluation_type = (
            marksheet_line_obj.marksheet_reg_id.exam_session_id
            and marksheet_line_obj.marksheet_reg_id.exam_session_id.evaluation_type
        )
        exam_details = []
        parent_subject_ids = []
        parent_obtained_total = 0
        parent_total = 0
        grades = self.env["xe.grade.configuration"].sudo().search([])
        parent_with_zero_marks = []
        for parent_subject_line in marksheet_line_obj.result_line_ids.filtered(
            lambda parent_sub: parent_sub.exam_id.subject_id.is_parent
            and parent_sub.exam_id.subject_id.show_on_report_card
        ):
            child_total_marks = 0
            child_total_obtained_marks = 0
            if (
                parent_subject_line.exam_id.subject_id.id not in parent_subject_ids
            ):  # for multiple parent same subject is there
                self.get_line_values(parent_subject_line, exam_details, is_child=False)
                having_child = (
                    self.env["xe.subject"]
                    .sudo()
                    .search(
                        [("parent_id", "=", parent_subject_line.exam_id.subject_id.id)]
                    )
                )
                if parent_subject_line.marks < 0:
                    parent_with_zero_marks.append(
                        parent_subject_line.exam_id.subject_id.name
                    )
                else:
                    if having_child:
                        parent_obtained_total += 0
                        parent_total += 0
                    else:
                        no_child_parent_percentage = int(
                            Decimal(
                                round(
                                    (
                                        parent_subject_line.marks
                                        / parent_subject_line.exam_id.total_marks
                                    )
                                    * 100,
                                    2,
                                )
                            ).to_integral_value(rounding=ROUND_HALF_UP)
                        )
                        parent_obtained_total += no_child_parent_percentage
                        parent_total += 100
                parent_subject_ids.append(parent_subject_line.exam_id.subject_id.id)
                child_total_marks = 0

                for child_subject_line in marksheet_line_obj.result_line_ids.filtered(
                    lambda child_sub: not child_sub.exam_id.subject_id.is_parent
                    and parent_subject_line.exam_id.subject_id.id
                    == child_sub.exam_id.subject_id.parent_id.id
                    and child_sub.exam_id.subject_id.show_on_report_card
                ):
                    self.get_line_values(
                        child_subject_line, exam_details, is_child=True
                    )
                    child_total_marks += child_subject_line.exam_id.total_marks
                    child_total_obtained_marks += child_subject_line.marks

            if child_total_obtained_marks:
                parent_sub_line = list(
                    filter(
                        lambda sub: sub["exam"]
                        == parent_subject_line.exam_id.subject_id.name,
                        exam_details,
                    )
                )
                parent_grade = False
                parent_subject_percentage = int(
                    Decimal(
                        round((child_total_obtained_marks / child_total_marks) * 100, 2)
                    ).to_integral_value(rounding=ROUND_HALF_UP)
                )
                parent_obtained_total += parent_subject_percentage
                parent_total += 100

                parent_grade = ""
                grade_category_ids = (
                    self.env["xe.grade.category"]
                    .sudo()
                    .search(
                        [
                            ("course_ids", "in", [course_id]),
                            (
                                "subject_ids",
                                "in",
                                [parent_subject_line.exam_id.subject_id.id],
                            ),
                        ],
                        limit=1,
                    )
                )
                if grade_category_ids:
                    for gc_line in grade_category_ids.grade_category_line_ids.filtered(
                        lambda gr: gr.min_per <= parent_subject_percentage <= gr.max_per
                    ):
                        parent_grade = gc_line.result

                parent_sub_line[0].update(
                    {
                        "obtained_marks": parent_subject_percentage,
                        "grade": parent_grade,
                    }
                )

        total_avg_mark = (
            parent_obtained_total
            and parent_total
            and int(
                Decimal(
                    round((parent_obtained_total / parent_total) * 100, 2)
                ).to_integral_value(rounding=ROUND_HALF_UP)
            )
            or 0
        )
        avg_grade = ""
        for grade in grades.filtered(
            lambda gr: gr.min_per <= total_avg_mark <= gr.max_per
        ):
            avg_grade = grade.result

        final_vals = {
            "exam_details": exam_details,
            "exam_type": marksheet_line_obj.exam_session_id.exam_type_id.name,
            "student": student,
            "exam_code": exam_code,
            "course": course,
            "exam_session": exam_session,
            "date": date,
            "total_marks": parent_total,
            "total_obtained_marks": parent_obtained_total,
            "total_percentage": parent_obtained_total
            and parent_total
            and round((parent_obtained_total / parent_total) * 100, 2)
            or 0,
            "total_status": total_status,
            "total_grade": total_grade,
            "evaluation_type": evaluation_type,
            "head_master_comment": marksheet_line_obj.head_master_comment or "",
            "head_teacher_comment": marksheet_line_obj.head_teacher_comment or "",
            "admission_no": admission_no,
            "classroom_name": classroom_name,
            "avg_grade": "",
            "head_teacher_signature": head_teacher_signature,
            "term_end_date": term_end_date,
            "opening_next_term_date": opening_next_term_date,
            "teacher_signature": teacher_signature,
        }
        return final_vals

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

    def get_line_values(self, result_line, exam_details, is_child):
        grade_category_ids = (
            self.env["xe.grade.category"]
            .sudo()
            .search(
                [
                    ("course_ids", "in", [result_line.marksheet_line_id.course_id.id]),
                    ("subject_ids", "in", [result_line.subject_id.id]),
                ],
                limit=1,
            )
        )
        if result_line.exam_id.subject_id.is_parent:
            parent_subject_percentage = int(
                Decimal(
                    round(
                        (result_line.marks / result_line.exam_id.total_marks) * 100, 2
                    )
                ).to_integral_value(rounding=ROUND_HALF_UP)
            )
            result_line.sudo().marks = parent_subject_percentage

        result_line.sudo().grade = ""
        if grade_category_ids:
            for gc_line in grade_category_ids.grade_category_line_ids:
                if (
                    gc_line.min_per
                    <= int(
                        Decimal(
                            round(
                                (result_line.marks / result_line.exam_id.total_marks)
                                * 100,
                                2,
                            )
                        ).to_integral_value(rounding=ROUND_HALF_UP)
                    )
                    <= gc_line.max_per
                ):
                    result_line.sudo().grade = gc_line.result

        values = {
            "exam": result_line.exam_id.subject_id
            and result_line.exam_id.subject_id.name,
            "exam_type": result_line.exam_id.session_id.exam_type_id.name,
            "total_marks": result_line.exam_id.total_marks,
            "minimum_marks": result_line.exam_id.min_marks,
            "obtained_marks": result_line.marks,
            "grade": result_line.grade,
            "comments": result_line.comments,
            "is_child": is_child,
            "hide_grade": result_line.exam_id.subject_id.hide_grade_on_report,
        }
        exam_details.append(values)


class ReportMarksheetLineReport(models.AbstractModel):
    _name = "report.xe_exam_management.report_combine_marksheetline_report"
    _description = "Exam Management Combine Marksheet Line Report"

    def get_details(self, marksheet_lines_obj, all_data):
        exam_details = []
        session = 0
        session_details = []
        mlt_sessions_total = []
        for marksheet_line_obj in marksheet_lines_obj:
            student = (
                marksheet_line_obj.student_id and marksheet_line_obj.student_id.name
            )
            course_id = marksheet_line_obj.course_id.id
            admission_no = marksheet_line_obj.student_id.roll_number
            classroom_name = marksheet_line_obj.student_id.classroom_id.name
            class_teacher_name = (
                marksheet_line_obj.student_id.course_id
                and marksheet_line_obj.student_id.course_id.head_teacher_id
                and marksheet_line_obj.student_id.course_id.head_teacher_id.name
                or ""
            )
            term_end_date = (
                marksheet_line_obj.marksheet_reg_id.exam_session_id
                and datetime.strftime(
                    marksheet_line_obj.marksheet_reg_id.exam_session_id.academic_term_id.end_date,
                    "%d/%m/%y",
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
            teacher_signature = (
                marksheet_line_obj.student_id.classroom_id.teacher_signature_html
            )
            head_teacher_signature = (
                marksheet_line_obj.student_id.classroom_id.course_id
                and marksheet_line_obj.student_id.classroom_id.course_id.head_teacher_signature
            )
            classroom_teacher_name = (
                marksheet_line_obj.student_id.classroom_id.teacher_id.name
                if marksheet_line_obj.student_id.classroom_id.teacher_id
                else ""
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
            evaluation_type = (
                marksheet_line_obj.marksheet_reg_id.exam_session_id
                and marksheet_line_obj.marksheet_reg_id.exam_session_id.evaluation_type
            )
            parent_subject_ids = []
            parent_obtained_total = 0
            total_subject = 0
            grades = self.env["xe.grade.configuration"].sudo().search([])
            parent_with_zero_marks = []
            for parent_subject_line in marksheet_line_obj.result_line_ids.filtered(
                lambda parent_sub: parent_sub.exam_id.subject_id.is_parent
                and parent_sub.exam_id.subject_id.show_on_report_card
            ):
                child_total_marks = 0
                child_total_obtained_marks = 0
                if (
                    parent_subject_line.exam_id.subject_id.id not in parent_subject_ids
                ):  # for multiple parent same subject is there
                    if not list(
                        filter(
                            lambda sub: sub["exam"]
                            == parent_subject_line.exam_id.subject_id.name,
                            exam_details,
                        )
                    ):
                        self.get_line_values(
                            parent_subject_line, exam_details, session, is_child=False
                        )
                    else:
                        self.another_session_vals(
                            parent_subject_line, exam_details, session
                        )
                    having_child = (
                        self.env["xe.subject"]
                        .sudo()
                        .search(
                            [
                                (
                                    "parent_id",
                                    "=",
                                    parent_subject_line.exam_id.subject_id.id,
                                )
                            ]
                        )
                    )
                    if parent_subject_line.marks < 0:
                        parent_with_zero_marks.append(
                            parent_subject_line.exam_id.subject_id.name
                        )
                    else:
                        if having_child:
                            parent_obtained_total += 0
                        else:
                            no_child_parent_percentage = int(
                                Decimal(
                                    round(
                                        (
                                            parent_subject_line.marks
                                            / parent_subject_line.exam_id.total_marks
                                        )
                                        * 100,
                                        2,
                                    )
                                ).to_integral_value(rounding=ROUND_HALF_UP)
                            )
                            parent_obtained_total += no_child_parent_percentage
                            total_subject += 1
                    parent_subject_ids.append(parent_subject_line.exam_id.subject_id.id)
                    child_total_marks = 0

                    for (
                        child_subject_line
                    ) in marksheet_line_obj.result_line_ids.filtered(
                        lambda child_sub: not child_sub.exam_id.subject_id.is_parent
                        and parent_subject_line.exam_id.subject_id.id
                        == child_sub.exam_id.subject_id.parent_id.id
                        and child_sub.exam_id.subject_id.show_on_report_card
                    ):
                        if not list(
                            filter(
                                lambda sub: sub["exam"]
                                == child_subject_line.exam_id.subject_id.name,
                                exam_details,
                            )
                        ):
                            self.get_line_values(
                                child_subject_line, exam_details, session, is_child=True
                            )
                        else:
                            self.another_session_vals(
                                child_subject_line, exam_details, session
                            )
                        child_total_marks += child_subject_line.exam_id.total_marks
                        child_total_obtained_marks += child_subject_line.marks

                if child_total_obtained_marks:
                    parent_sub_line = list(
                        filter(
                            lambda sub: sub["exam"]
                            == parent_subject_line.exam_id.subject_id.name,
                            exam_details,
                        )
                    )
                    parent_subject_percentage = int(
                        Decimal(
                            round(
                                (child_total_obtained_marks / child_total_marks) * 100,
                                2,
                            )
                        ).to_integral_value(rounding=ROUND_HALF_UP)
                    )
                    parent_obtained_total += parent_subject_percentage
                    total_subject += 1

                    parent_grade = ""
                    grade_category_ids = (
                        self.env["xe.grade.category"]
                        .sudo()
                        .search(
                            [
                                ("course_ids", "in", [course_id]),
                                (
                                    "subject_ids",
                                    "in",
                                    [parent_subject_line.exam_id.subject_id.id],
                                ),
                            ],
                            limit=1,
                        )
                    )
                    if grade_category_ids:
                        for (
                            gc_line
                        ) in grade_category_ids.grade_category_line_ids.filtered(
                            lambda gr: gr.min_per
                            <= parent_subject_percentage
                            <= gr.max_per
                        ):
                            parent_grade = gc_line.result

                    parent_sub_line[0].update(
                        {
                            "obtained_marks_%s" % (session): parent_subject_percentage,
                            "grade_%s" % (session): parent_grade,
                        }
                    )

            mlt_sessions_total.append(
                {
                    "obtained_marks_%s" % (session): parent_obtained_total,
                    "total_subject_%s" % (session): total_subject,
                    "avg_marks_%s" % (session): parent_obtained_total
                    and total_subject
                    and round((parent_obtained_total / total_subject), 2)
                    or 0,
                }
            )
            if session < 1:
                session_details.append(
                    {
                        "%s"
                        % (marksheet_line_obj.exam_session_id.academic_term_id.name): [
                            marksheet_line_obj.exam_session_id.exam_type_id.name
                        ],
                        "teacher_comment": (
                            marksheet_line_obj.head_master_comment + " "
                            if marksheet_line_obj.head_master_comment
                            else ""
                        ),
                        "extra_curr_comment": (
                            marksheet_line_obj.extra_curr_comment + " "
                            if marksheet_line_obj.extra_curr_comment
                            else ""
                        ),
                        "head_teacher_comment": (
                            marksheet_line_obj.head_teacher_comment + " "
                            if marksheet_line_obj.head_teacher_comment
                            else ""
                        ),
                    }
                )
            if session >= 1:
                session_details[0][
                    "%s" % (marksheet_line_obj.exam_session_id.academic_term_id.name)
                ].extend([marksheet_line_obj.exam_session_id.exam_type_id.name])
                session_details[0]["teacher_comment"] += (
                    marksheet_line_obj.head_master_comment
                    if marksheet_line_obj.head_master_comment
                    else ""
                )
                session_details[0]["extra_curr_comment"] += (
                    marksheet_line_obj.extra_curr_comment
                    if marksheet_line_obj.extra_curr_comment
                    else ""
                )
                session_details[0]["head_teacher_comment"] += (
                    marksheet_line_obj.head_teacher_comment
                    if marksheet_line_obj.head_teacher_comment
                    else ""
                )

            session += 1

        if all_data:
            final_vals = {
                "exam_details": exam_details,
                "student": student,
                "course": course,
                "exam_session": exam_session,
                "date": date,
                "evaluation_type": evaluation_type,
                "admission_no": admission_no,
                "classroom_name": classroom_name,
                "session": session,
                "session_details": session_details,
                "mlt_sessions_total": mlt_sessions_total,
                "classroom_teacher_name": classroom_teacher_name,
                "head_teacher_signature": head_teacher_signature,
                "class_teacher_name": class_teacher_name,
                "term_end_date": term_end_date,
                "opening_next_term_date": opening_next_term_date,
                "teacher_signature": teacher_signature,
            }
        else:
            final_vals = mlt_sessions_total
        return final_vals

    @api.model
    def _get_report_values(self, docids, data=None):
        marksheet_line_id = docids
        if data and data.get("form") and data["form"]["marksheet_line_id"]:
            marksheet_line_id = data["form"]["marksheet_line_id"]
        marksheet_line_obj = self.env["xe.marksheet.line"].browse(marksheet_line_id)
        marksheet_lines = (
            self.env["xe.marksheet.line"]
            .sudo()
            .search([("student_id", "=", marksheet_line_obj.student_id.id)])
        )
        marksheet_line_obj.exam_session_id.academic_term_id.name

        term_domain = [
            (
                "academic_term_id",
                "=",
                marksheet_line_obj.exam_session_id.academic_term_id.id,
            )
        ]
        class_domain = [("course_id", "=", marksheet_line_obj.course_id.id)]
        classroom_domain = [("classroom_id", "=", marksheet_line_obj.classroom_id.id)]

        class_students = self.env["xe.student"].sudo().search(class_domain)
        classroom_students = self.env["xe.student"].sudo().search(classroom_domain)

        class_wise_data = list()
        classroom_wise_data = list()

        for class_student in class_students:
            class_stu_lines = (
                self.env["xe.marksheet.line"]
                .sudo()
                .search(term_domain + [("student_id", "=", class_student.id)])
            )
            if class_stu_lines:
                class_wise_data.append(
                    {class_student.name: self.get_details(class_stu_lines, False)}
                )

        for classroom_student in classroom_students:
            classroom_stu_lines = (
                self.env["xe.marksheet.line"]
                .sudo()
                .search(term_domain + [("student_id", "=", classroom_student.id)])
            )
            if classroom_stu_lines:
                classroom_wise_data.append(
                    {
                        classroom_student.name: self.get_details(
                            classroom_stu_lines, False
                        )
                    }
                )

        class_positions, classroom_positions = self._get_positions(
            marksheet_line_obj.student_id.name, class_wise_data, classroom_wise_data
        )
        class_student_pos = self._get_student_positions(
            marksheet_line_obj.student_id.name, class_positions
        )
        classroom_student_pos = self._get_student_positions(
            marksheet_line_obj.student_id.name, classroom_positions
        )
        lines = []
        for marksheet_line in marksheet_lines:
            if (
                marksheet_line_obj.exam_session_id.academic_term_id.name
                == marksheet_line.exam_session_id.academic_term_id.name
            ):
                lines.append(marksheet_line)
        get_data = self.get_details(lines, True)
        get_data["class_position"] = class_student_pos
        get_data["classroom_position"] = classroom_student_pos
        docargs = {
            "doc_model": "xe.marksheet.line",
            "docs": marksheet_line_obj,
            "time": time,
            "get_lines": get_data,
        }
        return docargs

    def get_line_values(self, result_line, exam_details, session, is_child):
        result_line.sudo().grade = ""
        grade_category_ids = (
            self.env["xe.grade.category"]
            .sudo()
            .search(
                [
                    ("course_ids", "in", [result_line.marksheet_line_id.course_id.id]),
                    ("subject_ids", "in", [result_line.subject_id.id]),
                ],
                limit=1,
            )
        )
        if grade_category_ids:
            for gc_line in grade_category_ids.grade_category_line_ids:
                if (
                    gc_line.min_per
                    <= int(
                        Decimal(
                            round(
                                (result_line.marks / result_line.exam_id.total_marks)
                                * 100,
                                2,
                            )
                        ).to_integral_value(rounding=ROUND_HALF_UP)
                    )
                    <= gc_line.max_per
                ):
                    result_line.sudo().grade = gc_line.result

        values = {
            "exam": result_line.exam_id.subject_id
            and result_line.exam_id.subject_id.name,
            "exam_type": result_line.exam_id.session_id.exam_type_id.name,
            "total_marks": result_line.exam_id.total_marks,
            "minimum_marks": result_line.exam_id.min_marks,
            "obtained_marks_%s" % (session): result_line.marks,
            "grade_%s" % (session): result_line.grade,
            "comments": result_line.comments,
            "is_child": is_child,
            "hide_grade": result_line.exam_id.subject_id.hide_grade_on_report,
        }
        exam_details.append(values)

    def another_session_vals(self, result_line, exam_details, session):
        parent_sub_line = list(
            filter(
                lambda sub: sub["exam"] == result_line.exam_id.subject_id.name,
                exam_details,
            )
        )
        if result_line.exam_id.subject_id.is_parent:
            parent_subject_percentage = int(
                Decimal(
                    round(
                        (result_line.marks / result_line.exam_id.total_marks) * 100, 2
                    )
                ).to_integral_value(rounding=ROUND_HALF_UP)
            )
            result_line.sudo().marks = parent_subject_percentage

        result_line.sudo().grade = ""
        grade_category_ids = (
            self.env["xe.grade.category"]
            .sudo()
            .search(
                [
                    ("course_ids", "in", [result_line.marksheet_line_id.course_id.id]),
                    ("subject_ids", "in", [result_line.subject_id.id]),
                ],
                limit=1,
            )
        )
        if grade_category_ids:
            for gc_line in grade_category_ids.grade_category_line_ids:
                if (
                    gc_line.min_per
                    <= int(
                        Decimal(
                            round(
                                (result_line.marks / result_line.exam_id.total_marks)
                                * 100,
                                2,
                            )
                        ).to_integral_value(rounding=ROUND_HALF_UP)
                    )
                    <= gc_line.max_per
                ):
                    result_line.sudo().grade = gc_line.result

        parent_sub_line[0].update(
            {
                "obtained_marks_%s" % (session): result_line.marks,
                "grade_%s" % (session): result_line.grade,
            }
        )

    def _get_positions(self, student_name, class_data, classroom_data):
        class_list = list()
        classroom_list = list()

        for cl in class_data:
            for cl_key, cl_val in cl.items():
                cl_avg = 0
                for cl_list in cl_val:
                    cl_avg += sum(
                        [val for key, val in cl_list.items() if "avg_marks_" in key]
                    )
                class_list.append({cl_key: round(cl_avg, 2)})

        for clr in classroom_data:
            for clr_key, clr_val in clr.items():
                clr_avg = 0
                for clr_list in clr_val:
                    clr_avg += sum(
                        [val for key, val in clr_list.items() if "avg_marks_" in key]
                    )
                classroom_list.append({clr_key: round(clr_avg, 2)})

        class_position = ""
        classroom_position = ""
        if class_list:
            class_position = self.positions(class_list)
        if classroom_list:
            classroom_position = self.positions(classroom_list)
        return class_position, classroom_position

    def positions(self, stud_dict):
        new_stud_list = []
        for rec in stud_dict:
            new_stud_list.append({value: key for key, value in rec.items()})

        sorted_new_stud_dict = sorted(
            new_stud_list, key=lambda d: list(d.keys()), reverse=True
        )
        result = []
        for sort_dicts in sorted_new_stud_dict:
            for k, v in sort_dicts.items():
                if result:
                    if any(k in key for key in result):
                        for rec in result:
                            for key, val in rec.items():
                                if k == key:
                                    val.append(v)
                    else:
                        result.append({k: [v]})
                else:
                    result.append({k: [v]})

        position_result = []
        if result:
            count = 1
            for rec in result:
                for k, v in rec.items():
                    position_result.append({count: v})
                    count += 1
        return position_result

    def _get_student_positions(self, student, positions):
        rank = 0
        for pstn in positions:
            for k, v in pstn.items():
                if student in v:
                    rank = k
                    break
        return rank
