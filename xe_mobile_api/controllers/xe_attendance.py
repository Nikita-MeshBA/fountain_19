""" Attendance APIs python file """
# pylint: disable= E0401, C0116, R0801
from datetime import datetime
from odoo import http
from odoo.http import request


class XeAttendanceApi(http.Controller):
    """Attendance APIs"""

    def get_user_type(self):
        res = {}
        school_access_role = ""
        is_student = request.env.user.has_group("xenesis_school_base.group_xe_student")
        is_teacher = request.env.user.has_group("xenesis_school_base.group_xe_staff")
        is_parent = request.env.user.has_group("xenesis_school_base.group_xe_parent")
        is_back_office_admin = request.env.user.has_group(
            "xenesis_school_base.group_xe_admin"
        )
        if is_student:
            school_access_role = "student"
        if is_parent:
            school_access_role = "parent"
        if is_teacher:
            school_access_role = "teacher"
        if is_back_office_admin:
            school_access_role = "back_office_admin"
        res["school_access"] = school_access_role
        if school_access_role == "teacher":
            teacher_id = request.env["xe.staff"].search(
                [("partner_id", "=", request.env.user.partner_id.id)]
            )
            res["teacher_id"] = teacher_id.id
        elif school_access_role == "student":
            student_id = request.env["xe.student"].search(
                [("partner_id", "=", request.env.user.partner_id.id)]
            )
            res["student_id"] = student_id.id
        elif school_access_role == "parent":
            parent_id = request.env["xe.parent"].search(
                [("user_id", "=", request.env.user.id)]
            )
            res["parent_id"] = parent_id.id
        res["company_id"] = (
            request.env.user.company_id and request.env.user.company_id.id or False
        )
        return res

    def set_offset_limit(self, kw):
        offset, limit = 0, 0
        if kw.get("offset", False):
            offset = kw.get("offset")
        if kw.get("limit", False):
            limit = kw.get("limit")
        return offset, limit

    @http.route(
        "/v1/web/dataset/attendance/sheet/search_read", type="json", auth="user"
    )
    def get_attendance_sheet_list(self, args):
        attendances_list = []
        attendances = request.env["xe.student.attendance"].search(args[0])
        for res in attendances:
            attendance = {}
            attendance.setdefault("id", [res.id, res.name])
            attendance.setdefault("name", res.name)
            attendance.setdefault("state", res.state)
            attendance.setdefault("total_present", res.total_student_present)
            attendance.setdefault("total_absent", res.total_student_absent)
            attendance.setdefault(
                "register_id", [res.register_id.id, res.register_id.name]
            )

            attendance.setdefault("attendance_date", res.attendance_date)
            attendances_list.append(attendance)
            attendance_lines = []
            [
                attendance_lines.append(
                    {
                        "id": al.id,
                        "student_id": [al.student_id.id, al.student_id.name],
                        "present": al.present,
                        "remark": al.remark,
                    }
                )
                for al in res.attendance_details_ids
            ]
            attendance.setdefault("attendance_lines", attendance_lines)
        return attendances_list

    @http.route(
        "/v1/web/dataset/attendance/sheet/new/search_read", type="json", auth="user"
    )
    def get_attendance_sheet_list_new(self, **kw):
        user_type = self.get_user_type()
        attendances_list = []
        domain = [("company_id", "=", user_type.get("company_id")), ("state", "not in", ["cancel"])]
        is_user = request.env.user.has_group(
            "xe_attendance_management.group_s_attendance_user"
        )
        if is_user:
            domain.append(
                (
                    "attendance_register_id.allowed_teachers_ids.user_id",
                    "in",
                    [request.env.user.id],
                )
            )
        offset, limit = self.set_offset_limit(kw)
        if kw.get("search", False):
            domain.append(("name", "ilike", kw.get('search')))
        if kw.get("attendance_date", False):
            attendance_date = datetime.strptime(kw.get("attendance_date"), "%d/%m/%Y").date()
            domain.append(("attendance_date", "=", attendance_date))
        attendances = (
            request.env["xe.student.attendance"].sudo().search(domain, offset=offset, limit=limit, order="id desc")
        )
        for res in attendances:
            attendance = {}
            attendance.setdefault("id", [res.id, res.name])
            attendance.setdefault("name", res.name)
            attendance.setdefault("state", res.state)
            attendance.setdefault("total_present", res.total_student_present)
            attendance.setdefault("total_absent", res.total_student_absent)
            attendance.setdefault(
                "register_id",
                [res.attendance_register_id.id, res.attendance_register_id.name],
            )
            attendance.setdefault("attendance_date", res.attendance_date)
            attendances_list.append(attendance)
            attendance_lines = []
            [
                attendance_lines.append(
                    {
                        "id": al.id,
                        "student_id": [
                            al.student_id.id,
                            al.student_id.roll_number,
                            al.student_id.name,
                        ],
                        "attendance": al.attendance,
                        "remarks_type_id": [al.remarks_type_id.id, al.remarks_type_id.name],
                    }
                )
                for al in res.attendance_details_ids
            ]
            attendance.setdefault("attendance_lines", attendance_lines)
        return attendances_list

    @http.route("/v1/web/fetch/new-attendance-sheets", type="json", auth="user")
    def get_attendancesheets_by_reg_new(self, register_id, attendance_date):
        attendances_list = []
        domain = [("state", "not in", ["cancel"])]
        if register_id:
            domain.append(("attendance_register_id", "=", int(register_id)))
        if attendance_date:
            attendance_date = datetime.strptime(attendance_date, "%d/%m/%Y").date()
            domain.append(("attendance_date", "=", attendance_date))
        attendances = request.env["xe.student.attendance"].search(domain)
        for res in attendances:
            attendance = {}
            attendance.setdefault("id", [res.id, res.name])
            attendance.setdefault("name", res.name)
            attendance.setdefault("state", res.state)
            attendance.setdefault("total_present", res.total_student_present)
            attendance.setdefault("total_absent", res.total_student_absent)
            attendance.setdefault(
                "register_id",
                [res.attendance_register_id.id, res.attendance_register_id.name],
            )
            attendance.setdefault("attendance_date", res.attendance_date)
            attendances_list.append(attendance)
        return attendances_list

    @http.route("/v1/web/fetch/student/attendance-date", type="json", auth="user")
    def get_attendancesheets_by_student_date_new(self, student_id, attendance_date):
        user_type = self.get_user_type()
        fields = [
            "student_id",
            "roll_number",
            "attendance",
            "remarks_type_id",
            "attendance_id",
        ]
        domain = [
            ("company_id", "=", user_type.get("company_id")),
            ("student_id", "=", student_id),
            ("attendance_id.attendance_date", "=", attendance_date),
            ("attendance_id.state", "in", ["approved"]),
        ]
        student_attendance_details = (
            request.env["xe.attendance.details"].sudo().search_read(domain, fields)
        )
        return student_attendance_details

    @http.route(
        "/v1/web/dataset/attendance/sheet/fetch/students", type="json", auth="user"
    )
    def fetch_attendance_sheet_students(self, register_id):
        user_type = self.get_user_type()
        if user_type["school_access"] in ["student", "parent"]:
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User not allowed to do current xeeration",
                }
            }
        register = (
            request.env["xe.attendance.register"]
            .sudo()
            .search_read(
                [("id", "=", register_id)], ["id", "course_id", "class_room_id"]
            )
        )
        if not register:
            return {"students": [], "fetch_students": True}
        domain = [
            ("course_id", "=", register[0]["course_id"][0]),
        ]
        if register[0]["class_room_id"]:
            domain.append(("classroom_id", "=", register[0]["class_room_id"][0]))
        students = request.env["xe.student"].search(domain)
        students_ids = students.ids
        return {
            "students_ids": students_ids,
            "students": request.env["xe.student"]
            .sudo()
            .search_read([("id", "in", students_ids)], ["id", "name", "roll_number"]),
        }

    @http.route("/v1/web/fetch/remark-types", type="json", auth="user")
    def get_remarks_types(self):
        fields = ["name", "company_id"]
        result = request.env["xe.remarks.type"].search_read([], fields)
        return result

    @http.route("/v1/web/update/student/attendance-line", type="json", auth="user")
    def update_student_attendance_lines(self, args):
        update_list = args
        result_line = {}
        for record in update_list:
            line_id = record["id"]
            del record["id"]
            res = request.env["xe.attendance.details"].sudo().browse(line_id)
            record["mobile"] = True
            result = res.write(record)
            if not result:
                result_line["message"] = "Failed"
                result_line["flag"] = False
        if not result_line:
            result_line["message"] = "Success"
            result_line["flag"] = True
        return result_line

    @http.route("/attendance/search", type="json", auth="user")
    def get_attendance_search(self, **kw):
        attendances_list = []
        domain = [
            "|",
            "|",
            ("name", "ilike", kw.get("searchby")),
            ("attendance_register_id.name", "ilike", kw.get("searchby")),
            ("teacher_user_id.name", "ilike", kw.get("searchby")),
            ("state", "not in", ["cancel"]),
        ]
        attendances = (
            request.env["xe.student.attendance"].sudo().search(domain, order="id desc")
        )
        for res in attendances:
            attendance = {
                "id": [res.id, res.name],
                "name": res.name,
                "state": res.state,
                "total_present": res.total_student_present,
                "total_absent": res.total_student_absent,
                "register_id": [
                    res.attendance_register_id.id,
                    res.attendance_register_id.name,
                ],
                "attendance_date": res.attendance_date,
            }
            attendances_list.append(attendance)
            attendance_lines = []
            [
                attendance_lines.append(
                    {
                        "id": al.id,
                        "student_id": [
                            al.student_id.id,
                            al.student_id.roll_number,
                            al.student_id.name,
                        ],
                        "attendance": al.attendance,
                        "remarks": al.remarks,
                        "remarks_type_id": al.remarks_type_id.id,
                    }
                )
                for al in res.attendance_details_ids
            ]
            attendance["attendance_lines"] = attendance_lines
        return attendances_list

    @http.route("/attendance_sheet/buttons", type="json", auth="user")
    def set_attendance_sheet_buttons(self, **kw):
        user_type = self.get_user_type()

        attendance_sheet_id = (
            request.env["xe.student.attendance"]
            .sudo()
            .browse(kw.get("attendance_sheet_id"))
        )
        if kw.get("button", None) == "draft":
            attendance_sheet_id.state = "draft"

        if kw.get("button", None) == "confirm":
            attendance_details_ids = attendance_sheet_id.attendance_details_ids
            attendance_sheet_id.total_student_present = len(
                attendance_details_ids.filtered(lambda d: d.attendance == "present")
            )
            attendance_sheet_id.total_student_absent = len(
                attendance_details_ids.filtered(lambda d: d.attendance == "absent")
            )
            attendance_sheet_id.teacher_user_id = request.env.user.id
            attendance_sheet_id.state = "submitted"

        if kw.get("button", None) == "approve":
            if user_type["school_access"] != "back_office_admin":
                return {"message": "Access denied, please contact school administrator"}
            attendance_sheet_id.state = "approved"

        return {"message": "Success"}
