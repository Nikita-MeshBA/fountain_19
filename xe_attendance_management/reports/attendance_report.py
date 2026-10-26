# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import models, api


class StudentCard(models.AbstractModel):
    _name = "report.xe_attendance_management.report_student_attendance"
    _description = "xe_attendance_management Report Student Attendance"

    @api.model
    def _get_report_values(self, docids, data=None):
        from_date = False
        to_date = False
        course_id = False
        class_room_id = False
        attendance_state = False
        if "from_date" in data:
            from_date = data["from_date"]
        if "to_date" in data:
            to_date = data["to_date"]
        if "course_id" in data:
            course_id = int(data["course_id"])
        if "class_room_id" in data:
            class_room_id = int(data["class_room_id"])
        if "attendance_state" in data:
            attendance_state = data["attendance_state"]
        attendance_obj = self.env["xe.attendance.details"]
        domain = [("attendance_id.state", "not in", ["draft", "cancel"])]
        if from_date:
            domain.append(("attendance_date", ">=", from_date))
        if to_date:
            domain.append(("attendance_date", "<=", to_date))
        if course_id:
            domain.append(("course_id", "=", course_id))
        if class_room_id:
            domain.append(("class_room_id", "=", class_room_id))
        if attendance_state and attendance_state == "present":
            domain.append(("attendance", "=", "present"))
        if attendance_state and attendance_state == "absent":
            domain.append(("attendance", "=", "absent"))
        docs = attendance_obj.search(domain)
        student_lines = {}
        date_dict_docs = {}
        for line in docs:
            if line.attendance_date not in date_dict_docs:
                date_dict_docs[line.attendance_date] = [line]
            else:
                date_dict_docs[line.attendance_date].append(line)
        for line in docs:
            if line.student_id not in student_lines:
                student_lines[line.student_id] = {
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "half_day": 0,
                }
            if line.attendance == "present":
                student_lines[line.student_id]["present"] += 1
            if line.attendance == "absent":
                student_lines[line.student_id]["absent"] += 1

        return {
            "doc_ids": docs.ids,
            "doc_model": "xe.attendance.details",
            "docs": docs,
            "date_dict_docs": date_dict_docs,
            "data": data,
        }
