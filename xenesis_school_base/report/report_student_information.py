# -*- coding: utf-8 -*-

import time
from datetime import datetime

from odoo.exceptions import UserError, ValidationError

from odoo import api, models, _

total_column = {}
sub_total_column = {}


class ReportStudentInformation(models.AbstractModel):
    _name = "report.xenesis_school_base.report_studentinformation"
    _description = "Student Information Report"

    def get_grouped(self, val):
        from collections import defaultdict

        res = defaultdict(list)
        for v, k in val:
            res[k].append(v)
        result = [{"course_term_name": k, "line_ids": v} for k, v in res.items()]
        return result

    def _get_student_details(self, course_ids, term_ids, fees_filter):
        res = []
        if fees_filter == "classroom" and term_ids:
            student_academic_obj = self.env["xe.student"].search(
                [("classroom_id", "in", term_ids)]
            )
        elif fees_filter == "course" and course_ids:
            student_academic_obj = self.env["xe.student"].search(
                [("course_id", "=", course_ids)]
            )
        for obj in student_academic_obj:
            parent_names = ""
            student_id = obj.id
            student_name = obj.name
            dob = obj.dob
            roll_no = obj.roll_number
            gender = obj.gender
            email = obj.email
            course_name = obj.course_id.name
            class_room_name = obj.classroom_id.name
            term_name = obj.term_id and obj.term_id.name or ""
            if student_id:
                parent_details = self.env["xe.student.parent"].search(
                    [("student_id", "=", student_id)]
                )
                for parent in parent_details:
                    if parent.parent_id and parent.parent_id.name:
                        parent_names = parent.parent_id.name + "," + parent_names
            length_parent_name = len(parent_names)
            parent_names = parent_names[: (length_parent_name - 1)]
            student_course_rec = (
                self.env["xe.student.course"]
                .sudo()
                .search([("course_id", "=", obj.course_id.id)])
            )
            course_term_name = ""
            for sc in student_course_rec:
                term_name = sc.term_id and sc.term_id.name
                course_term_name = obj.course_id.name + "&" + sc.term_id.name
            if course_term_name:
                course_term_name = obj.course_id.name + "&" + obj.classroom_id.name
            if student_id:
                vals_tuple = (
                    {
                        "roll_no": roll_no,
                        "dob": dob,
                        "parent_name": parent_names,
                        "gender": gender,
                        "course_name": course_name,
                        "class_room_name": class_room_name,
                        "term_name": term_name,
                        "email": email,
                        "student_name": student_name,
                    },
                    course_term_name,
                )
                res.append(vals_tuple)
        grouped_dict = self.get_grouped(res)
        return grouped_dict

    @api.model
    def _get_report_values(self, docids, data=None):
        if (
            not data.get("form")
            or not self.env.context.get("active_model")
            or not self.env.context.get("active_id")
        ):
            raise UserError(
                _("Form content is missing, this report cannot be printed.")
            )
        model = self.env.context.get("active_model")
        docs = self.env[model].browse(self.env.context.get("active_id"))
        date = str(datetime.now()).split(".")[0]
        data["form"]["date"] = date
        course_ids = []
        if data["form"]["course_ids"]:
            course_ids = data["form"]["course_ids"]
        else:
            course_obj = self.env["xe.course"].search([])
            for course in course_obj:
                course_ids.append(course.id)
        if not course_ids:
            raise ValidationError(_("No Class Found in system"))
        term_ids = []
        if data["form"]["class_room_ids"]:
            term_ids = data["form"]["class_room_ids"]
        else:
            term_obj = self.env["xe.classroom"].search(
                [("course_id", "in", course_ids)]
            )
            for term in term_obj:
                term_ids.append(term.id)
        fees_filter = data["form"]["fees_filter"]
        details = self._get_student_details(course_ids, term_ids, fees_filter)

        final_result = []
        for info in details:
            info["term_name"] = data["form"]["classroom"]
            info["course_name"] = data["form"]["course"]
            final_result.append(info)
        return {
            "doc_ids": self.ids,
            "doc_model": model,
            "data": data["form"],
            "date": date,
            "docs": docs,
            "time": time,
            "get_details": final_result,
        }


class StudentInformationReportXlsx(models.AbstractModel):
    _name = "report.xenesis_school_base.report_student_information_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Student Information Report xlsx"

    def generate_xlsx_report(self, workbook, data, wizard):
        header_format = workbook.add_format(
            {"font_size": 15, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        header_format.set_center_across()
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 18, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("fee_analysis_report")
        data_format1 = workbook.add_format(
            {"font_size": 10, "align": "right", "font_name": "Arial"}
        )
        course = data["form"]["course"]
        class_room = data["form"]["classroom"]

        company_id = self.env.company
        if company_id:
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
            sheet.write(0, 1, company_id.name, format2)
            if company_address1:
                sheet.write(row1, 10, company_address1, format1)
            if company_address2:
                row1 += 1
                sheet.write(row1, 10, company_address2, format1)
            if company_address3:
                row1 += 1
                sheet.write(row1, 10, company_address3, format1)
            if company_address4:
                row1 += 1
                sheet.write(row1, 10, company_address4, format1)
            if company_id.website:
                row1 += 1
                sheet.write(row1, 10, company_id.website, format1)

            row = row1 + 2
        else:
            row = 2
        sheet.merge_range(row, 0, row, 8, "Student Parent Information", header_format)
        row += 1
        sheet.write(row, 0, "Class", format1)
        sheet.write(row, 1, course, format1)
        sheet.write(row, 3, "Class Room", format1)
        sheet.write(row, 4, class_room, format1)

        row += 2
        sheet.write(row, 0, "Admission Number", format1)
        sheet.write(row, 1, "Student Name", format1)
        sheet.write(row, 2, "Email", format1)
        sheet.write(row, 3, "Birth Date (DDMMYYYY)", format1)
        sheet.write(row, 4, "Class", format1)
        sheet.write(row, 5, "Class Room", format1)
        sheet.write(row, 6, "Academic Year", format1)
        sheet.write(row, 7, "Gender", format1)
        sheet.write(row, 8, "Joined Academic Year", format1)
        sheet.write(row, 9, "Blood Group", format1)
        sheet.write(row, 10, "Parent Name", format1)
        sheet.write(row, 11, "Parent Email", format1)
        sheet.write(row, 12, "Parent Mobile", format1)
        sheet.write(row, 13, "Parent Phone", format1)

        course_ids = []
        if data["form"]["course_ids"]:
            course_ids = data["form"]["course_ids"]
        else:
            course_obj = self.env["xe.course"].search([])
            for course in course_obj:
                course_ids.append(course.id)
        if not course_ids:
            raise ValidationError(_("No Class Found in system"))
        term_ids = []
        if data["form"]["class_room_ids"]:
            term_ids = data["form"]["class_room_ids"]
        else:
            term_obj = self.env["xe.classroom"].search(
                [("course_id", "in", course_ids)]
            )
            for term in term_obj:
                term_ids.append(term.id)
        fees_filter = data["form"]["fees_filter"]
        details = self._get_student_details(course_ids, term_ids, fees_filter)

        final_result = []
        for info in details:
            info["course"] = info.get("course_name")
            final_result.append(info)

        row += 1
        for res in final_result:
            for datas in res["line_ids"]:
                sheet.write(row, 0, datas["roll_no"], data_format1)
                sheet.write(row, 1, datas["student_name"], data_format1)
                sheet.write(row, 2, datas["email"], data_format1)
                sheet.write(row, 3, datas["dob"], data_format1)
                sheet.write(row, 4, datas["course_name"], data_format1)
                sheet.write(row, 5, datas["class_room_name"], data_format1)
                sheet.write(row, 6, datas["academic_year_id"], data_format1)
                sheet.write(row, 7, datas["gender"], data_format1)
                sheet.write(row, 8, datas["joined_date"], data_format1)
                sheet.write(row, 9, datas["blood_group"], data_format1)
                sheet.write(row, 10, datas["parent_name"], data_format1)
                sheet.write(row, 11, datas["parent_email"], data_format1)
                sheet.write(row, 12, datas["parent_mobile"], data_format1)
                sheet.write(row, 13, datas["parent_phone"], data_format1)
                row += 1

    def get_grouped(self, val):
        from collections import defaultdict

        res = defaultdict(list)
        for v, k in val:
            res[k].append(v)
        result = [{"course_name": k, "line_ids": v} for k, v in res.items()]
        return result

    def _get_student_details(self, course_ids, term_ids, fees_filter):
        res = []
        term_name = ""
        if fees_filter == "classroom" and term_ids:
            student_academic_obj = self.env["xe.student"].search(
                [("classroom_id", "in", term_ids)]
            )
        elif fees_filter == "course" and course_ids:
            student_academic_obj = self.env["xe.student"].search(
                [("course_id", "=", course_ids)]
            )
        for obj in student_academic_obj:
            student_name = obj.name
            d = obj.dob
            if d:
                dob = "-".join(str(d) for d in (d.day, d.month, d.year))
            else:
                dob = ""

            roll_no = obj.roll_number
            if obj.gender == "male":
                gender = "Male"
            elif obj.gender == "female":
                gender = "Female"
            email = obj.email if obj.email else ""
            joined_date = obj.joined_date if obj.joined_date else ""
            current_academic_year_id = (
                obj.current_academic_year_id.name if obj.current_academic_year_id else ""
            )
            academic_year_id = obj.academic_year_id.name if obj.academic_year_id else ""
            blood_group = obj.blood_group if obj.blood_group else ""
            course_name = obj.course_id.name
            class_room_name = obj.classroom_id.name

            count = 1
            if obj.parent_ids:
                for p in obj.parent_ids:
                    student_course_rec = (
                        self.env["xe.student.course"]
                        .sudo()
                        .search([("course_id", "=", obj.course_id.id)])
                    )
                    term_name = ""
                    for sc in student_course_rec:
                        term_name = sc.term_id and sc.term_id.name
                    if count == 1:
                        vals_tuple = (
                            {
                                "roll_no": roll_no,
                                "dob": dob,
                                "parent_name": p.name if p.name else "",
                                "parent_email": p.email if p.email else "",
                                "parent_mobile": p.mobile if p.phone else "",
                                "parent_phone": p.phone if p.phone else "",
                                "gender": gender,
                                "course_name": course_name,
                                "class_room_name": class_room_name,
                                "term_name": term_name,
                                "joined_date": academic_year_id,
                                "blood_group": blood_group,
                                "academic_year_id": current_academic_year_id,
                                "email": email,
                                "student_name": student_name,
                            },
                            obj.course_id.name,
                        )
                        res.append(vals_tuple)
                        count = count + 1
                    else:
                        vals_tuple = (
                            {
                                "roll_no": "",
                                "dob": "",
                                "parent_name": p.name if p.name else "",
                                "parent_email": p.email if p.email else "",
                                "parent_mobile": p.mobile if p.phone else "",
                                "parent_phone": p.phone if p.phone else "",
                                "gender": "",
                                "course_name": "",
                                "class_room_name": "",
                                "term_name": "",
                                "joined_date": "",
                                "blood_group": "",
                                "academic_year_id": "",
                                "email": "",
                                "student_name": "",
                            },
                            obj.course_id.name,
                        )
                        res.append(vals_tuple)
            else:
                vals_tuple = (
                    {
                        "roll_no": roll_no,
                        "dob": dob,
                        "parent_name": "",
                        "parent_email": "",
                        "parent_mobile": "",
                        "parent_phone": "",
                        "gender": gender,
                        "course_name": course_name,
                        "class_room_name": class_room_name,
                        "term_name": term_name,
                        "joined_date": joined_date,
                        "blood_group": blood_group,
                        "academic_year_id": academic_year_id,
                        "email": email,
                        "student_name": student_name,
                    },
                    obj.course_id.name,
                )
                res.append(vals_tuple)
        grouped_dict = self.get_grouped(res)
        return grouped_dict
