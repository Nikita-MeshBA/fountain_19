# -*- coding: utf-8 -*-

import collections
import functools
import operator
import time
from datetime import datetime

from odoo.exceptions import UserError
from odoo.tools import groupby

from odoo import models, api, _


class ReportMarksheetReport(models.AbstractModel):
    _name = "report.xe_exam_management.report_marksheet_report_new"

    def find_average(
        self, opener, opener_out, midterm, midterm_out, endterm, endterm_out
    ):
        opener_marks_100 = 0
        midterm_marks_100 = 0
        endterm_marks_100 = 0
        if opener_out != 0:
            opener_marks_100 = float(float(opener) / float(opener_out)) * 100
        else:
            opener_marks_100 = 0
        if midterm_out != 0:
            midterm_marks_100 = float(float(midterm) / float(midterm_out)) * 100
        else:
            midterm_marks_100 = 0
        if endterm_out != 0:
            endterm_marks_100 = float(float(endterm) / float(endterm_out)) * 100
        else:
            endterm_marks_100 = 0
        average = float(
            float(opener_marks_100 + midterm_marks_100 + endterm_marks_100) / 3
        )

        return average

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

    def find_grade(self, average):
        grade = ""
        grades = (
            self.env["xe.grade.configuration"].search(
                [("min_per", "<=", average), ("max_per", ">=", average)]
            )
            and self.env["xe.grade.configuration"].search(
                [("min_per", "<=", average), ("max_per", ">=", average)]
            )[0]
            or False
        )
        if grades:
            grade = grades.result
        return grade

    def findout_term_marks(
        self, student_id, course_id, term_id, term_obj, exam_session_id
    ):
        (
            opener_start_date,
            opener_end_date,
            mid_start_date,
            mid_end_date,
            end_start_date,
            end_end_date,
        ) = False
        lines = []
        total_opener = 0
        total_midterm = 0
        total_endterm = 0
        total_openerterm_marks = total_midterm_marks = total_endterm_marks = 0
        total_opener_outoff = 0
        total_midterm_outoff = 0
        total_endterm_outoff = 0
        for sub in exam_session_id.exam_ids:
            for subject in sub.subject_id:
                subjects = []
                subjects.append(subject.id)
                parent_subject = subject.parent_id and subject.parent_id.id or False
                if subject.show_on_report_card:
                    subject_dict = {
                        "subject": subject and subject.name,
                        "opener": 0,
                        "opener_outoff": 0,
                        "midterm": 0,
                        "midterm_outoff": 0,
                        "endterm": 0,
                        "endterm_outoff": 0,
                        "open_term_marks": 0,
                        "mid_term_marks": 0,
                        "end_term_marks": 0,
                        "open_term_avg": 0,
                        "mid_term_avg": 0,
                        "end_term_avg": 0,
                        "sequence": subject.sequence,
                    }

                    result_line = self.env["xe.result.line"].search(
                        [
                            ("related_course_id", "=", course_id),
                            ("student_id", "=", student_id),
                            ("subject_id", "in", subjects),
                        ]
                    )

                    child_sub = child_sub_rec = []
                    if len(result_line) >= 2:
                        for l in result_line:
                            vals = {result_line.subject_id.name: float(l.marks)}
                            child_sub_rec.append(vals)
                            child_sub.append(result_line.subject_id.name)

                    opener = 0
                    midterm = 0
                    endterm = 0
                    opener_outoff = 0
                    midterm_outoff = 0
                    endterm_outoff = 0
                    avg = 0

                    for line in result_line:
                        exam_start_date = line.start_time.date()
                        result_comment = line.comments

                        exam_end_date = line.end_time.date()
                        if (
                            opener_start_date
                            and opener_start_date <= exam_start_date
                            and opener_end_date
                            and opener_end_date >= exam_end_date
                        ):
                            if subject_dict["subject"] in child_sub:
                                result = dict(
                                    functools.reduce(
                                        operator.add,
                                        map(collections.Counter, child_sub_rec),
                                    )
                                )
                                if result.get(subject_dict["subject"]):
                                    opener = result.get(subject_dict["subject"]) / 2
                                    subject_dict["end_term_marks"] = opener
                            else:
                                opener = line.marks
                                subject_dict["opener"] += opener
                                # Add opener term marks
                            subject_dict["open_term_marks"] += opener
                            opener_outoff = line.total_marks
                            subject_dict["opener_outoff"] += opener_outoff
                            result_line_rec = self.env["xe.result.line"].search(
                                [
                                    ("related_course_id", "=", course_id),
                                    ("student_id", "=", student_id),
                                    (
                                        "subject_id",
                                        "in",
                                        exam_session_id.exam_ids.subject_id.ids,
                                    ),
                                ]
                            )
                            total_openerterm_marks = sum(
                                result_line_rec.mapped("marks")
                            )

                        if (
                            mid_start_date
                            and mid_start_date <= exam_start_date
                            and mid_end_date
                            and mid_end_date >= exam_end_date
                        ):
                            if subject_dict["subject"] in child_sub:
                                result = dict(
                                    functools.reduce(
                                        operator.add,
                                        map(collections.Counter, child_sub_rec),
                                    )
                                )
                                if result.get(subject_dict["subject"]):
                                    midterm = result.get(subject_dict["subject"]) / 2
                                    subject_dict["end_term_marks"] = midterm
                            else:
                                midterm = line.marks
                                subject_dict["midterm"] += midterm
                                # Add mid term marks
                                subject_dict["midterm_outoff"] += midterm_outoff
                            midterm_outoff = line.total_marks
                            subject_dict["mid_term_marks"] += midterm
                            result_line_rec = self.env["xe.result.line"].search(
                                [
                                    ("related_course_id", "=", course_id),
                                    ("student_id", "=", student_id),
                                    (
                                        "subject_id",
                                        "in",
                                        exam_session_id.exam_ids.subject_id.ids,
                                    ),
                                ]
                            )
                            total_midterm_marks = sum(result_line_rec.mapped("marks"))

                        if (
                            end_start_date
                            and end_start_date <= exam_start_date
                            and end_end_date
                            and end_end_date >= exam_end_date
                        ):
                            if subject_dict["subject"] in child_sub:
                                result = dict(
                                    functools.reduce(
                                        operator.add,
                                        map(collections.Counter, child_sub_rec),
                                    )
                                )
                                if result.get(subject_dict["subject"]):
                                    endterm = result.get(subject_dict["subject"]) / 2
                                    subject_dict["end_term_marks"] = endterm
                            else:
                                endterm = line.marks
                                # Add end term marks
                                subject_dict["end_term_marks"] += endterm
                                subject_dict["endterm"] += endterm
                            result_line_rec = self.env["xe.result.line"].search(
                                [
                                    ("related_course_id", "=", course_id),
                                    ("student_id", "=", student_id),
                                    (
                                        "subject_id",
                                        "in",
                                        exam_session_id.exam_ids.subject_id.ids,
                                    ),
                                ]
                            )
                            total_endterm_marks = sum(result_line_rec.mapped("marks"))
                            endterm_outoff = line.total_marks
                            subject_dict["endterm_outoff"] += endterm_outoff

                        subject_dict["result_comment"] = result_comment
                        lines.append(subject_dict)

                    opener_percentage = subject_dict["opener_outoff"] / 100
                    if opener_percentage:
                        subject_dict["opener"] = round(
                            subject_dict["opener"] / opener_percentage, 2
                        )
                        subject_dict["opener_outoff"] = 100
                    midterm_percentage = subject_dict["midterm_outoff"] / 100
                    if midterm_percentage:
                        subject_dict["midterm"] = round(
                            subject_dict["midterm"] / midterm_percentage, 2
                        )
                        subject_dict["midterm_outoff"] = 100
                    endterm_percentage = subject_dict["endterm_outoff"] / 100
                    if endterm_percentage:
                        subject_dict["endterm"] = round(
                            subject_dict["endterm_outoff"] / endterm_percentage, 2
                        )
                        subject_dict["endterm_outoff"] = 100

                    subject_dict["avg"] = 0
                    subject_dict["rubrics"] = ""
                    subject_dict["grade"] = ""
                    # All term rubrics and grade callulation
                    if (
                        subject_dict["opener"]
                        and subject_dict["midterm"]
                        and subject_dict["endterm"]
                    ):
                        avg = round(
                            float(
                                subject_dict["opener"]
                                + subject_dict["midterm"]
                                + subject_dict["endterm"]
                            )
                            / float(3),
                            2,
                        )
                        subject_dict["avg"] = avg
                        subject_dict["rubrics"] = ""
                        subject_dict["grade"] = ""
                        if not parent_subject:
                            subject_dict["rubrics"] = self.find_rubrics(avg)
                            subject_dict["grade"] = self.find_grade(avg)
                    # Single term rubrics and grade callulation
                    elif (
                        subject_dict["open_term_marks"]
                        or subject_dict["mid_term_marks"]
                        or subject_dict["end_term_marks"]
                    ):
                        if subject_dict["open_term_marks"]:
                            avg = round(
                                float(subject_dict["open_term_marks"]) / float(1), 2
                            )
                        elif subject_dict["mid_term_marks"]:
                            avg = round(
                                float(subject_dict["mid_term_marks"]) / float(1), 2
                            )
                        elif subject_dict["end_term_marks"]:
                            avg = round(
                                float(subject_dict["end_term_marks"]) / float(1), 2
                            )
                        subject_dict["avg"] = avg
                        subject_dict["rubrics"] = self.find_rubrics(avg)
                        subject_dict["grade"] = self.find_grade(avg)

                    if not parent_subject:
                        total_opener = total_opener + subject_dict["opener"]
                        total_midterm = total_midterm + subject_dict["midterm"]
                        total_endterm = total_endterm + subject_dict["endterm"]
                        total_opener_outoff = (
                            total_opener_outoff + subject_dict["opener_outoff"]
                        )
                        total_midterm_outoff = (
                            total_midterm_outoff + subject_dict["midterm_outoff"]
                        )
                        total_endterm_outoff = (
                            total_endterm_outoff + subject_dict["endterm_outoff"]
                        )

        total_marks = {
            "total_opener": total_opener,
            "total_midterm": total_midterm,
            "total_endterm": total_endterm,
            "total_opener_outoff": total_opener_outoff,
            "total_midterm_outoff": total_midterm_outoff,
            "total_endterm_outoff": total_endterm_outoff,
            # Single term calcultion
            "open_term_marks": subject_dict["open_term_marks"],
            "mid_term_marks": subject_dict["mid_term_marks"],
            "end_term_marks": subject_dict["end_term_marks"],
            "total_openerterm_marks": total_openerterm_marks,
            "total_midterm_marks": total_midterm_marks,
            "total_endterm_marks": total_endterm_marks,
        }

        lines = [i for n, i in enumerate(lines) if i not in lines[n + 1 :]]
        lines = sorted(lines, key=lambda i: i["sequence"])
        return lines, total_marks

    def get_objects(self, objects):
        obj_list = []
        for obj in objects:
            obj_list.extend(obj)
        return obj_list

    def get_lines_default_format(self, obj, marksheet_line_id):
        lines = []
        marksheet_line = obj.marksheet_line
        if marksheet_line_id:
            marksheet_line = self.env["xe.marksheet.line"].browse(marksheet_line_id)
        for line in marksheet_line:
            lines.extend(line)
        return lines

    def get_lines(self, obj, marksheet_line_id):
        data = []
        marksheet_line = obj.marksheet_line
        date = str(datetime.now())[:10]
        if marksheet_line_id:
            marksheet_line = self.env["xe.marksheet.line"].browse(marksheet_line_id)
        for line in marksheet_line:
            student_name = line and line.student_id and line.student_id.name
            classroom_name = line and line.student_id.classroom_id.name or ""

            classroom_id = line and line.classroom_id and line.classroom_id.id or False
            student_id = line and line.student_id and line.student_id.id

            term_obj = line.exam_session_id.academic_term_id
            term_name = (
                line.exam_session_id.academic_term_id
                and line.exam_session_id.academic_term_id.name
            )

            header = "Student Report Card"
            general_comment = line.head_master_comment
            extra_comment = line.extra_curr_comment
            head_teacher_comment = line.head_teacher_comment

            course_id = (
                line.exam_session_id.course_id and line.exam_session_id.course_id.id
            )
            course_name = (
                line.exam_session_id.course_id and line.exam_session_id.course_id.name
            )
            grade_name = course_name + " " + classroom_name

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

            term_id = term_obj and term_obj.id
            term_end_date = (
                line.exam_session_id.academic_term_id
                and line.exam_session_id.academic_term_id.end_date
            )
            next_term_start = ""
            next_academic_year = (
                datetime.now()
                .date()
                .replace(month=1, day=1, year=datetime.now().year + 1)
            )
            next_academic_year_rec = (
                self.env["xe.academic.year"]
                .sudo()
                .search(
                    [
                        ("start_date", "<=", next_academic_year),
                        ("end_date", ">=", next_academic_year),
                        ("company_id", "=", self.env.user.company_id.id),
                    ]
                )
            )
            if next_academic_year_rec:
                next_term_obj = (
                    self.env["xe.academic.terms"]
                    .sudo()
                    .search(
                        [("academic_year", "=", next_academic_year_rec.id)], limit=1
                    )
                )
                next_term_start = next_term_obj.start_date

            c_position, c_length = self.compute_class_position(
                line, line.student_id, course_id, term_id, classroom_id
            )

            class_post_str = str(c_position) + " out of " + str(c_length)
            o_position, o_length = self.compute_over_position(
                line, line.student_id, course_id, term_id
            )

            overall_post_str = str(o_position) + " out of " + str(o_length)

            data_dict = {
                "student": student_name,
                "gr_no": line.student_id.roll_number,
                "grade": grade_name,
                "header": header,
                "next_term_date": next_term_start,
                "term_end_date": term_end_date,
                "term_name": term_name,
                "date": date,
                "general_comment": general_comment,
                "extra_comment": extra_comment,
                "head_teacher_comment": head_teacher_comment,
                "teacher_name": teacher_name,
                "head_teacher_name": head_teacher_name,
                "head_teacher_signature": head_teacher_signature,
                "teacher_signature": teacher_signature,
                "class_post_str": class_post_str,
                "overall_post_str": overall_post_str,
            }
            exam_session_id = line.exam_session_id
            lines, total_marks = self.findout_term_marks(
                student_id, course_id, term_id, term_obj, exam_session_id
            )

            data_dict["lines"] = lines
            data_dict["total_opener"] = total_marks["total_opener"]
            data_dict["total_mid"] = total_marks["total_midterm"]
            data_dict["total_end"] = total_marks["total_endterm"]
            data_dict["total_opener_outoff"] = total_marks["total_opener_outoff"]
            data_dict["total_midterm_outoff"] = total_marks["total_midterm_outoff"]
            data_dict["total_endterm_outoff"] = total_marks["total_endterm_outoff"]

            data_dict["total_openerterm_marks"] = total_marks["total_openerterm_marks"]
            data_dict["total_midterm_marks"] = total_marks["total_midterm_marks"]
            data_dict["total_endterm_marks"] = total_marks["total_endterm_marks"]
            total_avg = 0
            total_outoff = (
                data_dict["total_opener_outoff"]
                + data_dict["total_midterm_outoff"]
                + data_dict["total_endterm_outoff"]
                or 1
            )
            if total_outoff <= 0:
                total_avg = 0
            else:
                total_avg = round(
                    float(
                        data_dict["total_opener"]
                        + data_dict["total_mid"]
                        + data_dict["total_end"]
                    )
                    / 3,
                    2,
                )

            total_marks_obtained = (
                data_dict["total_opener"]
                + data_dict["total_mid"]
                + data_dict["total_end"]
            )
            total_percentage = float(
                round(total_marks_obtained / total_outoff, 2) * 100
            )

            total_avg_rubric = self.find_rubrics(total_percentage)
            total_avg_grade = self.find_grade(total_avg)

            data_dict["total_avg"] = total_avg
            data_dict["total_avg_rubric"] = total_avg_rubric
            data_dict["total_avg_grade"] = total_avg_grade
            data.append(data_dict)
        return data

    def get_lines_k_p_p(self, obj, marksheet_line_id):
        data = []
        marksheet_line = obj.marksheet_line
        if marksheet_line_id:
            marksheet_line = self.env["xe.marksheet.line"].browse(marksheet_line_id)
        for line in marksheet_line:
            student_name = line and line.student_id and line.student_id.name

            classroom_name = (
                line
                and line.student_id
                and line.student_id.course_detail_ids
                and line.student_id.classroom_id
                and line.student_id.classroom_id.name
                or ""
            )
            header2 = "Student Report Card"
            general_comment = line.head_master_comment
            extra_comment = line.extra_curr_comment
            head_teacher_comment = line.head_teacher_comment

            course_name = (
                line.exam_session_id.course_id and line.exam_session_id.course_id.name
            )
            grade_name = course_name + " " + classroom_name
            header1 = student_name + " " + "-" + " " + grade_name
            if line.student_id.roll_number:
                header1 = (
                    student_name
                    + " "
                    + "("
                    + line.student_id.roll_number
                    + ")"
                    + " "
                    + "-"
                    + " "
                    + grade_name
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
            teacher_name = (
                line.classroom_id.teacher_id and line.classroom_id.teacher_id.name or ""
            )
            teacher_signature = (
                line.classroom_id and line.classroom_id.teacher_signature_html or ""
            )
            term_end_date = (
                line.exam_session_id.term_id and line.exam_session_id.term_id.end_date
            )
            next_term_start = ""
            next_academic_year = (
                datetime.now()
                .date()
                .replace(month=1, day=1, year=datetime.now().year + 1)
            )
            next_academic_year_rec = (
                self.env["xe.academic.year"]
                .sudo()
                .search(
                    [
                        ("start_date", "<=", next_academic_year),
                        ("end_date", ">=", next_academic_year),
                        ("company_id", "=", self.env.user.company_id.id),
                    ]
                )
            )
            if next_academic_year_rec:
                next_term_obj = (
                    self.env["xe.academic.terms"]
                    .sudo()
                    .search(
                        [("academic_year", "=", next_academic_year_rec.id)], limit=1
                    )
                )
                next_term_start = next_term_obj.start_date

            data_dict = {
                "header1": header1,
                "header2": header2,
                "next_term_date": next_term_start,
                "term_end_date": term_end_date,
                "head_teacher_name": head_teacher_name,
                "head_teacher_signature": head_teacher_signature,
                "teacher_signature": teacher_signature,
                "general_comment": general_comment,
                "extra_comment": extra_comment,
                "head_teacher_comment": head_teacher_comment,
            }
            lines = []
            for r_line in line.result_line:
                result_dict = {
                    "subject": r_line.exam_id
                    and r_line.exam_id.subject_id
                    and r_line.exam_id.subject_id.name,
                    "comment": r_line.comments,
                    "teacher_name": teacher_name,
                    "general_comment": general_comment,
                    "extra_comment": extra_comment,
                    "head_teacher_comment": head_teacher_comment,
                    "rubrics": r_line.rubrics,
                }
                lines.append(result_dict)

            data_dict["lines"] = lines
            data.append(data_dict)
        return data

    def give_rank(self, array):
        srt = sorted(array, key=lambda x: x[1], reverse=True)
        rankings = []
        rank = 1
        for k, v in groupby(srt, lambda x: x[1]):
            grp = [(rank, tup[0]) for tup in v]
            rankings += grp
            rank += 1
        return rankings

    def add_duplicates(self, values):
        d = dict()
        for key, val in values:
            if key in d:
                d[key] += val
            else:
                d[key] = val
        list_new = [(k, v) for k, v in d.items()]
        return list_new

    def compute_class_position(
        self, marksheet_line, student_obj, course_id, term_id, classroom_id
    ):
        rank = 1
        student_id = student_obj and student_obj.id or False
        position_array = []
        same_obj = self.env["xe.marksheet.line"].search(
            [("course_id", "=", course_id), ("classroom_id", "=", classroom_id)]
        )
        for obj in same_obj:
            position_tuple = (obj.student_id.id, obj.total_marks)
            position_array.append(position_tuple)
        position_array = self.add_duplicates(position_array)
        ranked_list = self.give_rank(position_array)

        for item in ranked_list:
            list_item = list(item)
            if student_id == list_item[1]:
                rank = list_item[0]

        return rank, len(ranked_list)

    def compute_over_position(self, marksheet_line, student_obj, course_id, term_id):
        rank = 1
        student_id = student_obj and student_obj.id or False
        position_array = []
        same_obj = self.env["xe.marksheet.line"].search(
            [("course_id", "=", course_id), ("term_id", "=", term_id)]
        )
        for obj in same_obj:
            position_tuple = (obj.student_id.id, obj.total_marks)
            position_array.append(position_tuple)
        position_array = self.add_duplicates(position_array)
        ranked_list = self.give_rank(position_array)
        for item in ranked_list:
            list_item = list(item)
            if student_id == list_item[1]:
                rank = list_item[0]

        return rank, len(ranked_list)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["xe.marksheet.register"].browse(docids)
        docargs = {}
        evaluation_type = docs.evaluation_type
        course_name = docs.course_id and docs.course_id.name
        if not evaluation_type and "marksheet_reg_id" not in data:
            raise UserError(
                _(
                    f'There is no Evaluation Type defined for this Course: "{course_name}". '
                    f"You may have to define Evaluation Type field inside corresponding Course form"
                )
            )
        if evaluation_type == "8-4-4":
            docargs = {
                "doc_model": "xe.marksheet.register",
                "docs": docs,
                "time": time,
                "get_objects": self.get_objects,
                "get_lines": self.get_lines,
                "marksheet_line_id": False,
                "class_system": "8-4-4",
            }
        elif evaluation_type == "1-3 CBC":
            docargs = {
                "doc_model": "xe.marksheet.register",
                "docs": docs,
                "time": time,
                "get_objects": self.get_objects,
                "get_lines": self.get_lines,
                "marksheet_line_id": False,
                "class_system": "1-3 CBC",
            }
        elif evaluation_type in ("Kindergarten", "Playgroup", "Pre Primary"):
            docargs = {
                "doc_model": "xe.marksheet.register",
                "docs": docs,
                "time": time,
                "get_objects": self.get_objects,
                "get_lines": self.get_lines_k_p_p,
                "marksheet_line_id": False,
                "class_system": "K-P-P",
            }

        if "marksheet_reg_id" in data:
            marksheet_reg_id = int(data["marksheet_reg_id"])
            marksheet_line_id = int(data["marksheet_line_id"])
            evaluation_type = data["evaluation_type"]
            course_name = data["course_name"]
            if not evaluation_type:
                raise UserError(
                    _(
                        f'There is no Evaluation Type defined for this Course: "{course_name}".'
                        f"You may have to define Evaluation Type field "
                        f"inside corresponding Course form"
                    )
                )

            docs = self.env["xe.marksheet.register"].browse(marksheet_reg_id)
            if evaluation_type == "8-4-4":
                docargs = {
                    "doc_model": "xe.marksheet.register",
                    "docs": docs,
                    "time": time,
                    "get_objects": self.get_objects,
                    "get_lines": self.get_lines,
                    "marksheet_line_id": marksheet_line_id,
                    "class_system": "8-4-4",
                }

            elif evaluation_type == "1-3 CBC":
                docargs = {
                    "doc_model": "xe.marksheet.register",
                    "docs": docs,
                    "time": time,
                    "get_objects": self.get_objects,
                    "get_lines": self.get_lines,
                    "marksheet_line_id": marksheet_line_id,
                    "class_system": "1-3 CBC",
                }

            elif evaluation_type in ("Kindergarten", "Playgroup", "Pre Primary"):
                docargs = {
                    "doc_model": "xe.marksheet.register",
                    "docs": docs,
                    "time": time,
                    "get_objects": self.get_objects,
                    "get_lines": self.get_lines_k_p_p,
                    "marksheet_line_id": marksheet_line_id,
                    "class_system": "K-P-P",
                }

        return docargs
