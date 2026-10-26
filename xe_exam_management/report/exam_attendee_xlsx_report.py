from odoo import models


class ExamAttendeeXlsx(models.AbstractModel):
    _name = "report.xe_exam_management.report_exam_attendee_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Exam Attendee xlsx"

    def generate_xlsx_report(self, workbook, data, attendance):
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("attendance_report")
        row = 0
        sheet.write(row, 0, "External ID", format1)
        sheet.write(row, 1, "Student Name", format1)
        sheet.write(row, 2, "Marks", format1)
        sheet.write(row, 3, "Comments", format1)
        sheet.write(row, 4, "Exam/External ID", format1)
        # sheet.write(row, 4, "Note", format1)

        row = row + 1
        if data["form"]["exam_id"]:
            exam_id = (
                self.env["xe.exam"]
                .sudo()
                .search([("id", "=", data["form"]["exam_id"])])
            )
            attendee_rec = exam_id.attendees_line_ids
            for line in attendee_rec:
                attendee_external_id = line._export_rows([["id"]])[0][0]
                exam_external_id = exam_id._export_rows([["id"]])[0][0]
                comments = line.comments if line.comments else ""
                # note = line.note if line.note else ""
                sheet.write(row, 0, attendee_external_id, format2)
                sheet.write(row, 1, line.student_id.name, format2)
                sheet.write(row, 2, line.marks, format2)
                sheet.write(row, 3, comments, format2)
                sheet.write(row, 4, exam_external_id, format2)
                # sheet.write(row, 4, note, format2)
                row += 1
            sheet.set_column(0, 10, 20)
