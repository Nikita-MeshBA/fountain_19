import base64
import io
from odoo import models, fields

total_column = {}
sub_total_column = {}


class SchemeOfWorkXlsx(models.AbstractModel):
    _name = "report.xe_lesson_planner.report_scheme_of_work_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Scheme Of Work xlsx"

    def generate_xlsx_report(self, workbook, data, wizard):
        header_format = workbook.add_format(
            {"font_size": 15, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        header_format.set_center_across()
        format1 = workbook.add_format(
            {"font_size": 12, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 15, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("fee_analysis_report")
        data_format1 = workbook.add_format(
            {
                "font_size": 12,
                "align": "right",
                "font_name": "Arial",
                "bg_color": "#ccccb3",
            }
        )
        data_format2 = workbook.add_format(
            {
                "font_size": 12,
                "align": "right",
                "font_name": "Arial",
                "bg_color": "#b3b3b3",
            }
        )
        date_start = data["date_from"]
        date_end = data["date_to"]

        company_id = self.env["res.company"].browse(int(data["company"]))
        if company_id:
            product_image = company_id.logo
            imgdata = base64.b64decode(product_image)
            image = io.BytesIO(imgdata)

            image_width = 120.0
            image_height = 300.0

            cell_width = 80.0
            cell_height = 50.0

            x_scale = cell_width / image_width
            y_scale = cell_height / image_height

            sheet.insert_image(
                "A1",
                "myimage.png",
                {"image_data": image, "x_scale": x_scale, "y_scale": y_scale},
            )

            company_address1 = (
                company_address2
            ) = company_address3 = company_address4 = ""
            if company_id.street:
                company_address1 = company_id.street + ","
            if company_id.street2:
                company_address1 += company_id.street2
            if company_id.city:
                company_address2 = company_id.city + ","
            if company_id.state_id.name:
                company_address2 += company_id.state_id.name
            if company_id.country_id:
                company_address3 = company_id.country_id.name
            if company_id.email:
                company_address4 = company_id.email + ","
            if company_id.phone:
                company_address4 += company_id.phone
            row1 = 0
            sheet.write(0, 3, company_id.name, format2)
            if company_address1:
                sheet.write(row1, 6, company_address1, format1)
            if company_address2:
                row1 += 1
                sheet.write(row1, 6, company_address2, format1)
            if company_address3:
                row1 += 1
                sheet.write(row1, 6, company_address3, format1)
            if company_address4:
                row1 += 1
                sheet.write(row1, 6, company_address4, format1)
            if company_id.website:
                row1 += 1
                sheet.write(row1, 6, company_id.website, format1)

            row = row1 + 2
        else:
            row = 2
        sheet.merge_range(row, 0, row, 8, str(data["report_name"]), header_format)
        row += 1
        sheet.write(row, 0, "Start Date", format1)
        sheet.write(row, 1, date_start, format1)
        sheet.write(row, 3, "End Date", format1)
        sheet.write(row, 4, date_end, format1)

        if data.get("fees_filter") == "employee":
            employee_id = self.env["hr.employee"].browse([data["employee"]])
            data["employee"] = employee_id.name
            sheet.write(row, 6, "Employee", format1)
            sheet.write(row, 7, data["employee"], format1)
            domain = [("employee_id", "=", employee_id.id)]
            if date_start and date_end:
                domain += [
                    ("create_date", ">=", date_start),
                    ("create_date", "<=", date_end),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)
        elif data.get("fees_filter") == "department":
            department_id = self.env["hr.department"].browse([data["department"]])
            data["department"] = department_id.name
            sheet.write(row, 6, "Department", format1)
            sheet.write(row, 7, data["department"], format1)
            domain = [("department_id", "=", department_id.id)]
            if date_start and date_end:
                domain += [
                    ("create_date", ">=", date_start),
                    ("create_date", "<=", date_end),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)
        elif data.get("fees_filter") == "classroom":
            domain = [("classroom_id", "=", data["classroom"])]
            sheet.write(row, 6, "Class Room", format1)
            sheet.write(row, 7, data["classroom_name"], format1)
            if date_start and date_end:
                domain += [
                    ("create_date", ">=", date_start),
                    ("create_date", "<=", date_end),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)
        elif data.get("fees_filter") == "course" and data["course"]:
            domain = [("class_id", "=", data["course"])]
            sheet.write(row, 6, "Course", format1)
            sheet.write(row, 7, data["course_name"], format1)
            if date_start and date_end:
                domain += [
                    ("create_date", ">=", date_start),
                    ("create_date", "<=", date_end),
                ]
            scheme_of_work_rec = self.env["scheme.of.work"].search(domain)

        final_result = []
        for s in scheme_of_work_rec:
            subject = ""
            sub_name_list = s.assigned_sub_ids.mapped("name")
            for i in range(0, len(sub_name_list)):
                subject = "" + subject + sub_name_list[i] + ","

            name = s.employee_id.name
            grade = s.class_id.name
            grade_room = s.classroom_id.name
            subjects = subject
            if s.scheme_of_work_ids:
                for i in s.scheme_of_work_ids:
                    vals = {
                        "name": name,
                        "grade": grade,
                        "grade_room": grade_room,
                        "subjects": subjects,
                        "week": i.week,
                        "lesson": i.lesson,
                        "topic": i.topic,
                        "sub_topic": i.sub_topic,
                        "learning_activities": i.learning_activities,
                        "learning_resources": i.learning_resources,
                        "key_inquiry_questions": i.key_inquiry_questions,
                        "assessment_methods": i.assessment_methods,
                    }
                    final_result.append(vals)
            else:
                vals = {
                    "name": name,
                    "grade": grade,
                    "grade_room": grade_room,
                    "subjects": subjects,
                }
                final_result.append(vals)
        row += 2
        header_rows = [
            "Teacher",
            "Grade",
            "Grade Room",
            "Subject",
            "Lesson",
            "Strand",
            "Sub-Strand",
            "Learning Activities",
            "Learning Resources",
            "Key Inquiry Questions",
            "Assessment Methods",
            "Remarks",
        ]

        col = 0
        for h in range(0, len(header_rows)):
            sheet.write(row, col, header_rows[h], format1)
            col += 1
        row = row + 1
        for rec in range(0, len(final_result)):
            col = 0
            if (row % 2) == 0:
                cell_format = data_format1
            else:
                cell_format = data_format2

            sheet.write(row, col, final_result[rec]["name"], cell_format)
            sheet.write(row, col + 1, final_result[rec]["grade"], cell_format)
            sheet.write(row, col + 2, final_result[rec]["grade_room"], cell_format)
            sheet.write(row, col + 3, final_result[rec]["subjects"], cell_format)
            if final_result[rec].get("week"):
                sheet.write(row, col + 4, final_result[rec]["week"], cell_format)
            else:
                sheet.write(row, col + 4, "", cell_format)
            if final_result[rec].get("lesson"):
                sheet.write(row, col + 5, final_result[rec]["lesson"], cell_format)
            else:
                sheet.write(row, col + 5, "", cell_format)
            if final_result[rec].get("topic"):
                sheet.write(row, col + 6, final_result[rec]["topic"], cell_format)
            else:
                sheet.write(row, col + 6, "", cell_format)
            if final_result[rec].get("sub_topic"):
                sheet.write(row, col + 7, final_result[rec]["sub_topic"], cell_format)
            else:
                sheet.write(row, col + 7, "", cell_format)
            if final_result[rec].get("learning_activities"):
                sheet.write(
                    row, col + 8, final_result[rec]["learning_activities"], cell_format
                )
            else:
                sheet.write(row, col + 8, "", cell_format)
            if final_result[rec].get("learning_resources"):
                sheet.write(
                    row, col + 9, final_result[rec]["learning_resources"], cell_format
                )
            else:
                sheet.write(row, col + 9, "", cell_format)
            if final_result[rec].get("key_inquiry_questions"):
                sheet.write(
                    row,
                    col + 10,
                    final_result[rec]["key_inquiry_questions"],
                    cell_format,
                )
            else:
                sheet.write(row, col + 10, "", cell_format)
            if final_result[rec].get("assessment_methods"):
                sheet.write(
                    row, col + 11, final_result[rec]["assessment_methods"], cell_format
                )
            else:
                sheet.write(row, col + 11, "", cell_format)

            row = row + 1
