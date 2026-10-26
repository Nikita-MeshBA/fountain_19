# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from datetime import datetime

from odoo import models


class AttendanceSummaryXlsx(models.AbstractModel):
    _name = "report.xe_attendance_management.attendance_summary_xlsx"
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
        docs = attendance_obj.search(domain)
        student_ids = docs.mapped("student_id").ids
        unique_students = set(student_ids)
        heading = workbook.add_format(
            {"font_size": 14, "align": "center", "bold": True, "font_name": "Arial"}
        )
        format1 = workbook.add_format(
            {"font_size": 12, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 11, "align": "vcenter", "font_name": "Arial"}
        )
        format3 = workbook.add_format(
            {"font_size": 11, "align": "right", "font_name": "Arial"}
        )
        format4 = workbook.add_format(
            {"font_size": 11, "align": "right", "font_name": "Arial", "bold": True}
        )
        sheet = workbook.add_worksheet("attendance_report")
        sheet.merge_range(0, 0, 0, 5, "Student Attendance Summary", heading)
        row = 1

        date_from = datetime.strptime(data["form"]["from_date"], "%Y-%m-%d").strftime(
            "%d-%m-%Y"
        )
        date_to = datetime.strptime(data["form"]["to_date"], "%Y-%m-%d").strftime(
            "%d-%m-%Y"
        )

        sheet.write(row, 1, "Date From", format1)
        sheet.write(row, 2, date_from, format1)
        sheet.write(row, 3, "Date To", format1)
        sheet.write(row, 4, date_to, format1)
        row += 1
        course_name = self.env["xe.course"].browse(data["form"]["course_id"]).name
        classroom = self.env["xe.classroom"].browse(data["form"]["class_room_id"]).name
        sheet.write(row, 1, "Class", format1)
        sheet.write(row, 2, course_name, format1)
        sheet.write(row, 3, "Classroom", format1)
        sheet.write(row, 4, classroom, format1)
        row += 1

        sheet.write(row, 0, "Admission Number", format1)
        sheet.write(row, 1, "Student Name", format1)
        sheet.write(row, 2, "Gender", format1)
        sheet.write(row, 3, "Attendance Sessions", format1)
        sheet.write(row, 4, "Present Sessions", format1)
        sheet.write(row, 5, "Attendance Percentage", format1)
        student_objs = self.env["xe.student"].browse(unique_students)
        total_percentage = 0
        for obj in student_objs:
            row += 1
            sheet.write(row, 0, obj.roll_number, format2)
            sheet.write(row, 1, obj.name, format2)
            sheet.write(
                row,
                2,
                dict(obj.fields_get(allfields=["gender"])["gender"]["selection"])[
                    obj.gender
                ],
                format2,
            )
            total_sessions = len(docs.filtered(lambda d: d.student_id.id == obj.id))
            attended_sessions = docs.filtered(
                lambda d: d.student_id.id == obj.id and d.attendance == "present"
            )
            attendance_session = len(attended_sessions)
            attendance_perc = 0
            if total_sessions:
                attendance_perc = round((attendance_session / total_sessions) * 100, 2)
            total_percentage += attendance_perc
            attendance_perc = str(attendance_perc) + "%"
            sheet.write(row, 3, total_sessions, format2)
            sheet.write(row, 4, attendance_session, format3)
            sheet.write(row, 5, attendance_perc, format3)
        row += 1
        avg_perc = 0
        if len(student_objs) > 0:
            avg_perc = round(total_percentage / len(student_objs), 2)
        sheet.write(row, 4, "Class Average Percentage", format1)
        avg_perc = str(avg_perc) + "%"
        sheet.write(row, 5, avg_perc, format4)
        sheet.set_column(0, 10, 25)
