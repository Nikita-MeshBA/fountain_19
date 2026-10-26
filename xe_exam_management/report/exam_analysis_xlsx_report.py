from odoo import models


class ExamAnalysisXlsx(models.AbstractModel):
    _name = "report.xe_exam_management.report_exam_analysis_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Exam Analysis xlsx"

    def generate_xlsx_report(self, workbook, data, attendance):
        heading = workbook.add_format(
            {
                "font_size": 11,
                "align": "center",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
            }
        )
        format1 = workbook.add_format(
            {
                "font_size": 9,
                "align": "left",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
            }
        )
        format2 = workbook.add_format(
            {
                "font_size": 9,
                "align": "left",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
            }
        )
        sheet = workbook.add_worksheet("analysis_report")

        row = 0
        sheet.merge_range(row, 0, row, 8, str(data["report_name"]), heading)

        analysis_type = data["form"]["analysis_type"]
        course_id = data["form"]["course_id"]
        classroom_ids = data["form"]["classroom_ids"]
        domain = [
            ("session_id", "=", data["form"]["session_id"]),
            ("state", "=", "done"),
        ]
        if course_id:
            domain.append(("course_id", "=", course_id))
        if classroom_ids:
            domain.append(("classroom_ids", "in", classroom_ids))
        if analysis_type == "exam_session_wise":
            exam_rec = self.env["xe.exam"].sudo().search(domain)
        else:
            subject_ids = data["form"]["subject_ids"]
            subjects = self.env["xe.subject"].search(
                ["|", ("id", "in", subject_ids), ("parent_id", "in", subject_ids)]
            )
            for sub in subjects:
                if sub.id not in subject_ids:
                    subject_ids.append(sub.id)
            if subject_ids:
                domain.append(("subject_id", "in", subject_ids))
            exam_rec = self.env["xe.exam"].sudo().search(domain)
        row += 3
        student_list = []
        student_classroom_list = []

        for exam in exam_rec:
            for attend in exam.attendees_line_ids:
                if attend.student_id.name not in student_list:
                    student_list.append(attend.student_id.name)
                    student_classroom_list.append(attend.student_id.classroom_id.name)

        # End - Fetch Student and marks based on subject
        subject_stud_data = list()
        subject_total_marks_list = list()

        for exam in exam_rec:
            if any(exam.subject_id.name in key for key in subject_stud_data):
                continue
            else:
                subject_stud_data.append({exam.subject_id.name: []})
                if exam.total_marks:
                    subject_total_marks_list.append(
                        {exam.subject_id.name: [exam.total_marks]}
                    )

        # Students Added in data
        for exam in exam_rec:
            for attend in exam.attendees_line_ids:
                for subject in subject_stud_data:
                    for key1, val1 in subject.items():
                        if key1 == exam.subject_id.name:
                            val1 += [{attend.student_id.name: attend.marks}]

        child_row = row - 1
        sheet.write(row, 0, "No", format1)
        sheet.write(row, 1, "Name", format1)
        sheet.write(row, 2, "Classroom", format1)
        child_sub_col = 3
        stud_row = child_row + 2
        stud_col = 3

        row += 1
        for stud in range(0, len(list(set(student_list)))):
            sheet.write(row, 0, stud + 1, format1)
            sheet.write(row, 1, student_list[stud], format1)
            sheet.write(row, 2, student_classroom_list[stud], format1)
            row = row + 1
        row += 1
        sheet.write(row + 1, 1, "Total", format1)
        sheet.write(row + 2, 1, "Average", format1)
        sheet.write(row + 3, 1, "Percentage", format1)

        students_grandtotal = []
        for std in student_list:
            students_grandtotal.append({std: []})

        for subject in subject_stud_data:
            for sub_key, sub_val in subject.items():
                subject_mark = [
                    x[sub_key] for x in subject_total_marks_list if sub_key in x
                ]

                sheet.write(child_row, child_sub_col, sub_key, format1)
                sheet.write(
                    child_row + 1,
                    child_sub_col,
                    "Out of %s" % subject_mark[0][0],
                    format1,
                )

                total_marks = 0
                for student in student_list:
                    if not any(student in st for st in sub_val):
                        sub_val.append({student: 0})
                    for stud_dict in sub_val:
                        if stud_dict.get(student) or stud_dict.get(student)==0:
                            sheet.write(
                                stud_row, stud_col, stud_dict.get(student), format1
                            )
                            total_marks += stud_dict.get(student)
                            stud_row += 1

                            for std in students_grandtotal:
                                for std_key, std_val in std.items():
                                    if std_key == student:
                                        std_val.append(stud_dict.get(student))
                stud_row += 2

                average_marks = float(total_marks / len(student_list))
                percentage = float((average_marks / subject_mark[0][0]) * 100)
                sheet.write(stud_row, stud_col, total_marks, format1)
                sheet.write(stud_row + 1, stud_col, "%.2f" % average_marks, format2)
                sheet.write(stud_row + 2, stud_col, "%.2f" % percentage, format2)

                child_sub_col += 1
            stud_col += 1
            stud_row = 4

        gt_stud_row = 4
        gt_total = 0
        avg_total = 0

        # Add Grandtotal, Average, Position
        gt_total_marks = self._get_grandtotal_marks(subject_total_marks_list)
        sheet.write(child_row, child_sub_col, "Grand Total", format1)
        sheet.write(child_row + 1, child_sub_col, "Out of %s" % gt_total_marks, format1)
        sheet.merge_range(
            child_row,
            child_sub_col + 1,
            child_row + 1,
            child_sub_col + 1,
            "Average",
            workbook.add_format(
                {
                    "font_size": 9,
                    "align": "center",
                    "valign": "top",
                    "bold": True,
                    "font_name": "Arial",
                    "border": 1,
                }
            ),
        )

        for student in student_list:
            for stud_dict in students_grandtotal:
                for st_key, st_val in stud_dict.items():
                    if st_key == student:
                        gt_total += sum(st_val)
                        avg_total += float(sum(st_val) / len(subject_stud_data))
                        sheet.write(gt_stud_row, child_sub_col, sum(st_val), format1)
                        sheet.write(
                            gt_stud_row,
                            child_sub_col + 1,
                            "%.2f" % float(sum(st_val) / len(subject_stud_data)),
                            format2,
                        )
                        gt_stud_row += 1

        gt_stud_row += 1
        gt_average = 0
        gt_percentage = 0
        avg_average = 0
        avg_percentage = 0

        try:
            gt_average += float(gt_total / len(student_list))
        except:
            gt_average += 0
        try:
            gt_percentage += float((gt_average / gt_total_marks) * 100)
        except:
            gt_percentage += 0
        try:
            avg_average += float(avg_total / len(student_list))
        except:
            avg_average += 0
        try:
            avg_percentage += float((avg_average / 100) * 100)
        except:
            avg_percentage += 0

        sheet.write(gt_stud_row + 1, child_sub_col, gt_total, format1)
        sheet.write(gt_stud_row + 2, child_sub_col, "%.2f" % gt_average, format2)
        sheet.write(gt_stud_row + 3, child_sub_col, "%.2f" % gt_percentage, format2)
        sheet.write(gt_stud_row + 1, child_sub_col + 1, avg_total, format1)
        sheet.write(gt_stud_row + 2, child_sub_col + 1, "%.2f" % avg_average, format2)
        sheet.write(
            gt_stud_row + 3, child_sub_col + 1, "%.2f" % avg_percentage, format2
        )
        # sheet.autofit()
        sheet.set_column(0, 0, 2)

    def _get_positions(self, stud_dict):
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

    def _get_subject_total_marks(self, child_key, parent_key, subject_total_marks_list):
        marks_total = 0
        for total_marks in subject_total_marks_list:
            for key_parent, val_parent in total_marks.items():
                if key_parent == parent_key:
                    for sub_total_marks in val_parent:
                        for key_sub_child, val_sub_child in sub_total_marks.items():
                            if key_sub_child == child_key:
                                marks_total += sum(val_sub_child)
                                break
                    break
        return marks_total

    def _get_grandtotal_marks(self, subject_total_marks_list):
        marks_total = 0
        for total_marks in subject_total_marks_list:
            for key_parent, val_parent in total_marks.items():
                marks_total += sum(val_parent)
        return marks_total
