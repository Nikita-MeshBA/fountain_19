# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models


class AttendanceXlsx(models.AbstractModel):
    _name = "report.xe_attendance_management.attendance_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Attendance xlsx"

    def generate_xlsx_report(self, workbook, data, attendance):
        attendance_obj = self.env["xe.attendance.details"]

        domain = [("attendance_id.state", "not in", ["draft", "cancel"])]
        if data["form"]["from_date"]:
            domain.append(("attendance_date", ">=", data["form"]["from_date"]))
        if data["form"]["to_date"]:
            domain.append(("attendance_date", "<=", data["form"]["to_date"]))
        if data["form"]["course_id"]:
            domain.append(("course_id", "=", data["form"]["course_id"]))
        if data["form"]["class_room_id"]:
            domain.append(("class_room_id", "=", data["form"]["class_room_id"]))
        if (
            data["form"]["attendance_state"]
            and data["form"]["attendance_state"] == "present"
        ):
            domain.append(("attendance", "=", "present"))
        if (
            data["form"]["attendance_state"]
            and data["form"]["attendance_state"] == "absent"
        ):
            domain.append(("attendance", "=", "absent"))
        docs = attendance_obj.search(domain)
        date_dict_docs = {}
        for line in docs:
            if line.attendance_date not in date_dict_docs:
                date_dict_docs[line.attendance_date] = [line]
            else:
                date_dict_docs[line.attendance_date].append(line)
        heading = workbook.add_format(
            {"font_size": 13, "align": "center", "bold": True, "font_name": "Arial"}
        )
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("attendance_report")
        sheet.merge_range(0, 0, 0, 7, "Student Attendance Report", heading)
        row = 2
        sheet.write(row, 0, "Date From", format1)
        sheet.write(row, 1, data["form"]["from_date"], format1)
        sheet.write(row, 2, "Date To", format1)
        sheet.write(row, 3, data["form"]["to_date"], format1)
        row += 2
        if date_dict_docs:
            last_attendance_date = False
            attendance_obj = False
            for data_row in date_dict_docs:
                sheet.write(row, 0, "Admission Number", format1)
                sheet.write(row, 1, "Student Name", format1)
                sheet.write(row, 2, "Class", format1)
                sheet.write(row, 3, "Classroom", format1)
                sheet.write(row, 4, "Attendance Sheet", format1)
                sheet.write(row, 5, "Attendance Date", format1)
                sheet.write(row, 6, "Day", format1)
                sheet.write(row, 7, "Status", format1)
                row += 1
                data_lines = date_dict_docs[data_row]

                total_male_present = 0
                total_male_absent = 0
                total_female_present = 0
                total_female_absent = 0

                total_male_present_morning = 0
                total_male_absent_morning = 0
                total_female_present_morning = 0
                total_female_absent_morning = 0

                total_male_present_afternoon = 0
                total_male_absent_afternoon = 0
                total_female_present_afternoon = 0
                total_female_absent_afternoon = 0
                for line in data_lines:
                    sheet.write(row, 0, line.roll_number, format2)
                    sheet.write(row, 1, line.student_id.name, format2)
                    sheet.write(
                        row,
                        2,
                        line.attendance_id.attendance_register_id.course_id.name or "",
                        format2,
                    )
                    sheet.write(
                        row,
                        3,
                        line.attendance_id.attendance_register_id.class_room_id.name
                        or "",
                        format2,
                    )
                    sheet.write(row, 4, line.attendance_id.name, format2)
                    sheet.write(
                        row, 5, line.attendance_date.strftime("%d-%m-%Y"), format2
                    )
                    sheet.write(row, 6, line.attendance_date.strftime("%A"), format2)
                    sheet.write(
                        row,
                        7,
                        dict(
                            line.fields_get(allfields=["attendance"])["attendance"][
                                "selection"
                            ]
                        )[line.attendance],
                        format2,
                    )
                    last_attendance_date = line.attendance_date
                    attendance_obj = line.attendance_id

                    if line.attendance_id.attendance_session == "morning":
                        if (
                            line.attendance == "present"
                            and line.student_id.gender == "male"
                        ):
                            total_male_present_morning += 1
                        if (
                            line.attendance == "absent"
                            and line.student_id.gender == "male"
                        ):
                            total_male_absent_morning += 1
                        if (
                            line.attendance == "present"
                            and line.student_id.gender == "female"
                        ):
                            total_female_present_morning += 1
                        if (
                            line.attendance == "absent"
                            and line.student_id.gender == "female"
                        ):
                            total_female_absent_morning += 1
                    if line.attendance_id.attendance_session == "afternoon":
                        if (
                            line.attendance == "present"
                            and line.student_id.gender == "male"
                        ):
                            total_male_present_afternoon += 1
                        if (
                            line.attendance == "absent"
                            and line.student_id.gender == "male"
                        ):
                            total_male_absent_afternoon += 1
                        if (
                            line.attendance == "present"
                            and line.student_id.gender == "female"
                        ):
                            total_female_present_afternoon += 1
                        if (
                            line.attendance == "absent"
                            and line.student_id.gender == "female"
                        ):
                            total_female_absent_afternoon += 1
                    row += 1
                total_data = attendance_obj.get_total_data(
                    last_attendance_date, data["form"]
                )
                row += 1
                if total_data["attendance_type"] == "daily_2":
                    sheet.write(row, 0, "Total Students", format1)
                    sheet.write(row, 1, total_data["total_students"], format1)
                    sheet.write(row, 2, "Total Present Morning", format1)
                    sheet.write(row, 3, total_data["total_present_morning"], format1)
                    sheet.write(row, 4, "Total Absent Morning", format1)
                    sheet.write(row, 5, total_data["total_absent_morning"], format1)
                    row += 1
                    sheet.write(row, 0, "Total Present Afternoon", format1)
                    sheet.write(row, 1, total_data["total_present_afternoon"], format1)
                    sheet.write(row, 2, "Total Absent Afternoon", format1)
                    sheet.write(row, 3, total_data["total_absent_afternoon"], format1)

                    row += 1
                    sheet.write(row, 0, "Total Male Present Morning", format1)
                    sheet.write(row, 1, total_male_present_morning, format1)
                    sheet.write(row, 2, "Total Male Absent Morning", format1)
                    sheet.write(row, 3, total_male_absent_morning, format1)
                    row += 1
                    sheet.write(row, 0, "Total Female Present Morning", format1)
                    sheet.write(row, 1, total_female_present_morning, format1)
                    sheet.write(row, 2, "Total Female Absent Morning", format1)
                    sheet.write(row, 3, total_female_absent_morning, format1)

                    row += 1
                    sheet.write(row, 0, "Total Male Present Afternoon", format1)
                    sheet.write(row, 1, total_male_present_afternoon, format1)
                    sheet.write(row, 2, "Total Male Absent Afternoon", format1)
                    sheet.write(row, 3, total_male_absent_afternoon, format1)
                    row += 1
                    sheet.write(row, 0, "Total Female Present Afternoon", format1)
                    sheet.write(row, 1, total_female_present_afternoon, format1)
                    sheet.write(row, 2, "Total Female Absent Afternoon", format1)
                    sheet.write(row, 3, total_female_absent_afternoon, format1)
                else:
                    sheet.write(row, 0, "Total Students", format1)
                    sheet.write(row, 1, total_data["total_students"], format1)
                    sheet.write(row, 2, "Total Present", format1)
                    sheet.write(row, 3, total_data["total_present"], format1)
                    sheet.write(row, 4, "Total Absent", format1)
                    sheet.write(row, 5, total_data["total_absent"], format1)
                    row += 1
                    sheet.write(row, 0, "Total Male Present", format1)
                    sheet.write(row, 1, total_male_present, format1)
                    sheet.write(row, 2, "Total Male Absent", format1)
                    sheet.write(row, 3, total_male_absent, format1)
                    row += 1
                    sheet.write(row, 0, "Total Female Present", format1)
                    sheet.write(row, 1, total_female_present, format1)
                    sheet.write(row, 2, "Total Female Absent", format1)
                    sheet.write(row, 3, total_female_absent, format1)
                row += 2

        sheet.set_column(0, 10, 20)
