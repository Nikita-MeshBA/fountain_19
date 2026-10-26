from datetime import datetime
import time
from odoo import models, api
from decimal import Decimal, ROUND_HALF_UP


class CbcCombineMarksheetLineReport(models.AbstractModel):
    _name = "report.xe_exam_management.cbc_combine_marksheetline"
    _description = "CBC Combine Marksheet Line Report"

    def get_details(self, marksheet_lines_obj, all_data):
        exam_details = []
        session = 0
        session_details = []
        mlt_sessions_total = []
        marksheet_lines_obj = sorted(marksheet_lines_obj, key=lambda line: line.exam_session_id.start_date)
        for marksheet_line_obj in marksheet_lines_obj:
            student = (
                marksheet_line_obj.student_id and marksheet_line_obj.student_id.name
            )
            admission_no = marksheet_line_obj.student_id.roll_number
            classroom_name = marksheet_line_obj.student_id.classroom_id.name
            class_teacher_name = (
                marksheet_line_obj.student_id.course_id
                and marksheet_line_obj.student_id.course_id.head_teacher_id
                and marksheet_line_obj.student_id.course_id.head_teacher_id.name
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
            academic_year_id = (
                marksheet_line_obj.academic_year_id
                and marksheet_line_obj.academic_year_id.name
                or ""
            )
            term_end_date = marksheet_line_obj.academic_term_id and datetime.strftime(
                marksheet_line_obj.academic_term_id.end_date,
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
            header_section = (
                marksheet_line_obj.student_id.classroom_id.course_id
                and marksheet_line_obj.student_id.classroom_id.course_id.section
                and marksheet_line_obj.student_id.classroom_id.course_id.section.upper()
                or ""
            )

            parent_subject_ids = []
            parent_obtained_total = 0
            total_subject = 0
            grades = self.env["xe.grade.configuration"].sudo().search([])
            parent_with_zero_marks = []
            term_name = (
                marksheet_line_obj.marksheet_reg_id.exam_session_id.academic_term_id.name
                + " "
                + str(date1.year)
                + " "
                + "Progress Report"
            )

            for parent_subject_line in marksheet_line_obj.result_line_ids.filtered(
                lambda parent_sub: parent_sub.exam_id.subject_id.show_on_report_card
            ):
                if parent_subject_line.exam_id.subject_id.is_parent:
                    child_total_marks = 0
                    child_total_obtained_marks = 0
                    if (
                        parent_subject_line.exam_id.subject_id.id
                        not in parent_subject_ids
                    ):  # for multiple parent same subject is there
                        if not list(
                            filter(
                                lambda sub: sub["exam"]
                                == parent_subject_line.exam_id.subject_id.name,
                                exam_details,
                            )
                        ):
                            self.get_line_values(
                                parent_subject_line,
                                exam_details,
                                session,
                                is_child=False,
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
                        parent_subject_ids.append(
                            parent_subject_line.exam_id.subject_id.id
                        )
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
                                    child_subject_line,
                                    exam_details,
                                    session,
                                    is_child=True,
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
                        parent_grade = False
                        parent_subject_percentage = int(
                            Decimal(
                                round(
                                    (child_total_obtained_marks / child_total_marks)
                                    * 100,
                                    2,
                                )
                            ).to_integral_value(rounding=ROUND_HALF_UP)
                        )
                        parent_obtained_total += parent_subject_percentage
                        total_subject += 1
                        for grade in grades.filtered(
                            lambda gr: gr.min_per
                            <= parent_subject_percentage
                            <= gr.max_per
                        ):
                            parent_grade = grade.result
                        parent_sub_line[0].update(
                            {
                                "obtained_marks_%s"
                                % (session): parent_subject_percentage,
                                "grade_%s" % (session): parent_grade,
                            }
                        )
                else:
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

            mlt_sessions_total.append(
                {
                    "obtained_marks_%s" % (session): parent_obtained_total,
                    "total_subject_%s" % (session): total_subject,
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

        self.get_average_and_rubrics(exam_details)

        if all_data:
            final_vals = {
                "term_name": term_name,
                "exam_details": self.set_subject_sequence(exam_details),
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
                "teacher_signature": teacher_signature,
                "term_end_date": term_end_date,
                "opening_next_term_date": opening_next_term_date,
                "academic_year_id": academic_year_id,
                "header_section": header_section,
                "rubrics_data": self.get_rubrics(
                    marksheet_lines_obj[0].company_id.id,
                    marksheet_lines_obj[0].exam_session_id.id,
                ),
                "marks_mean": self._get_marks_mean(exam_details, session),
            }
        else:
            final_vals = self.set_subject_sequence(exam_details)
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
        # marksheet_line_obj.exam_session_id.academic_term_id.name

        # term_domain = [
        #     (
        #         "academic_term_id",
        #         "=",
        #         marksheet_line_obj.exam_session_id.academic_term_id.id,
        #     )
        # ]
        # class_domain = [("course_id", "=", marksheet_line_obj.course_id.id)]
        # classroom_domain = [("classroom_id", "=", marksheet_line_obj.classroom_id.id)]

        # class_students = self.env["xe.student"].sudo().search(class_domain)
        # classroom_students = self.env["xe.student"].sudo().search(classroom_domain)

        # class_wise_data = list()
        # classroom_wise_data = list()

        # for class_student in class_students:
        #     class_stu_lines = (
        #         self.env["xe.marksheet.line"]
        #         .sudo()
        #         .search(term_domain + [("student_id", "=", class_student.id)])
        #     )
        #     if class_stu_lines:
        #         class_wise_data.append(
        #             {class_student.name: self.get_details(class_stu_lines, False)}
        #         )

        # for classroom_student in classroom_students:
        #     classroom_stu_lines = (
        #         self.env["xe.marksheet.line"]
        #         .sudo()
        #         .search(term_domain + [("student_id", "=", classroom_student.id)])
        #     )
        #     if classroom_stu_lines:
        #         classroom_wise_data.append(
        #             {
        #                 classroom_student.name: self.get_details(
        #                     classroom_stu_lines, False
        #                 )
        #             }
        #         )

        # class_positions, classroom_positions = self._get_positions(
        #     marksheet_line_obj.student_id.name, class_wise_data, classroom_wise_data
        # )
        # class_student_pos = self._get_student_positions(
        #     marksheet_line_obj.student_id.name, class_positions
        # )
        # classroom_student_pos = self._get_student_positions(
        #     marksheet_line_obj.student_id.name, classroom_positions
        # )

        lines = []
        for marksheet_line in marksheet_lines:
            if (
                marksheet_line_obj.exam_session_id.academic_term_id.id
                == marksheet_line.exam_session_id.academic_term_id.id
            ):
                lines.append(marksheet_line)
        get_data = self.get_details(lines, True)
        # get_data["class_position"] = class_student_pos
        # get_data["classroom_position"] = classroom_student_pos
        docargs = {
            "doc_model": "xe.marksheet.line",
            "docs": marksheet_line_obj,
            # "time": time,
            "get_lines": get_data,
            "company": marksheet_line_obj.company_id,
        }
        return docargs

    def get_line_values(self, result_line, exam_details, session, is_child):
        grades = self.env["xe.grade.configuration"].sudo().search([])
        for grade in grades:
            if (
                grade.min_per
                <= int(
                    Decimal(
                        round(
                            (result_line.marks / result_line.exam_id.total_marks) * 100,
                            2,
                        )
                    ).to_integral_value(rounding=ROUND_HALF_UP)
                )
                <= grade.max_per
            ):
                result_line.sudo().grade = grade.result

        values = {
            "exam": result_line.exam_id.subject_id
            and result_line.exam_id.subject_id.name,
            "sequence": result_line.exam_id.subject_id
            and result_line.exam_id.subject_id.sequence,
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
        grades = self.env["xe.grade.configuration"].sudo().search([])
        for grade in grades:
            if (
                grade.min_per
                <= int(
                    Decimal(
                        round(
                            (result_line.marks / result_line.exam_id.total_marks) * 100,
                            2,
                        )
                    ).to_integral_value(rounding=ROUND_HALF_UP)
                )
                <= grade.max_per
            ):
                result_line.sudo().grade = grade.result
        parent_sub_line[0].update(
            {
                "obtained_marks_%s" % (session): result_line.marks,
                "grade_%s" % (session): result_line.grade,
            }
        )

    def get_average_and_rubrics(self, exam_details):
        rubrics_id = self.env["xe.rubrics.configuration"].search(
            [("exam_session_id", "=", False)]
        )
        for exam in exam_details:
            total_marks = 0
            count = 0
            average = 0
            for key, val in exam.items():
                if "obtained_marks_" in key:
                    total_marks += val
                    count += 1

            if total_marks and count:
                average = "%.2f" % float(total_marks / count)
                exam["average"] = float(average)
                rount_average = round(float(average))
                if rount_average and rubrics_id:
                    for rubrics in rubrics_id:
                        if rubrics.min_per <= rount_average <= rubrics.max_per:
                            exam["rubrics"] = rubrics.name
                else:
                    exam["rubrics"] = ""
            else:
                exam["average"] = float(0)
                exam["rubrics"] = ""

    # def _get_positions(self, student_name, class_data, classroom_data):
    #     class_list = list()
    #     classroom_list = list()

    #     for cl in class_data:
    #         for cl_key, cl_val in cl.items():
    #             cl_avg = 0
    #             for cl_list in cl_val:
    #                 cl_avg += sum(
    #                     [val for key, val in cl_list.items() if "average" in key]
    #                 )
    #             class_list.append({cl_key: round(cl_avg, 2)})

    #     for clr in classroom_data:
    #         for clr_key, clr_val in clr.items():
    #             clr_avg = 0
    #             for clr_list in clr_val:
    #                 clr_avg += sum(
    #                     [val for key, val in clr_list.items() if "average" in key]
    #                 )
    #             classroom_list.append({clr_key: round(clr_avg, 2)})

    #     class_position = ""
    #     classroom_position = ""
    #     if class_list:
    #         class_position = self.positions(class_list)
    #     if classroom_list:
    #         classroom_position = self.positions(classroom_list)
    #     return class_position, classroom_position

    # def positions(self, stud_dict):
    #     new_stud_list = []
    #     for rec in stud_dict:
    #         new_stud_list.append({value: key for key, value in rec.items()})

    #     sorted_new_stud_dict = sorted(
    #         new_stud_list, key=lambda d: list(d.keys()), reverse=True
    #     )
    #     result = []
    #     for sort_dicts in sorted_new_stud_dict:
    #         for k, v in sort_dicts.items():
    #             if result:
    #                 if any(k in key for key in result):
    #                     for rec in result:
    #                         for key, val in rec.items():
    #                             if k == key:
    #                                 val.append(v)
    #                 else:
    #                     result.append({k: [v]})
    #             else:
    #                 result.append({k: [v]})

    #     position_result = []
    #     if result:
    #         count = 1
    #         for rec in result:
    #             for k, v in rec.items():
    #                 position_result.append({count: v})
    #                 count += 1
    #     return position_result

    # def _get_student_positions(self, student, positions):
    #     rank = 0
    #     for pstn in positions:
    #         for k, v in pstn.items():
    #             if student in v:
    #                 rank = k
    #                 break
    #     return rank

    def set_subject_sequence(self, exam_details):
        new_exam_details = sorted(exam_details, key=lambda i: (i["sequence"]))
        return new_exam_details

    def get_rubrics(self, company_id, session_id):
        rubrics_id = self.env["xe.rubrics.configuration"].search_read(
            [
                ("company_id", "=", company_id),
                ("exam_session_id", "=", False),
                ("subject_id", "=", False),
            ],
            ["name", "min_per", "max_per"],
            order="id ASC",
        )
        return rubrics_id

    def _get_marks_mean(self, exam_details, session):
        marks_mean = []
        for i in range(0, session):
            data = {
                "marks_" + str(i): 0,
                "marks_count_" + str(i): 0,
                "total_marks_" + str(i): 0,
                "total_marks_count_" + str(i): 0,
            }

            for exam in exam_details:
                if exam.get("obtained_marks_" + str(i)):
                    data["marks_" + str(i)] += exam.get("obtained_marks_" + str(i))
                    data["marks_count_" + str(i)] += 1

                if exam.get("total_marks"):
                    data["total_marks_" + str(i)] += exam.get("total_marks")
                    data["total_marks_count_" + str(i)] += 1

            data["mean_" + str(i)] = float(
                (data["marks_" + str(i)]) / (data["marks_count_" + str(i)])
            )
            data["total_mean_" + str(i)] = float(
                (data["total_marks_" + str(i)]) / (data["total_marks_count_" + str(i)])
            )
            marks_mean.append(data)

        total_avg = 0
        avg_count = 0
        mean_avg = 0
        for e in exam_details:
            if e.get("average"):
                total_avg += e.get("average")
                avg_count += 1

        if total_avg:
            mean_avg += float(total_avg / avg_count)

        marks_mean.append(
            {
                "total_avg": total_avg,
                "mean_avg": mean_avg,
            }
        )

        return marks_mean
