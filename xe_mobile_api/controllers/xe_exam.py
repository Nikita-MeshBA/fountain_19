""" Exam APIs python file """
# pylint: disable= E0401, C0116, W0718, R1710, R0801
import json
import logging
from odoo import http
from odoo.http import request
from odoo.tools import groupby
from ..controllers.main import set_offset_limit

_logger = logging.getLogger(__name__)


class XeExamApi(http.Controller):
    """Exam APIs"""

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

    @http.route("/v1/web/dataset/fetch/exams/details", type="json", auth="user")
    def fetch_attendance_exam_details(self, exam_id):
        user_type = self.get_user_type()
        if user_type["school_access"] in ["student", "parent"]:
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User not allowed to do current xeeration",
                }
            }
        fetched_exam = (
            request.env["xe.exam"].sudo().search_read([("id", "=", int(exam_id))])
        )
        if not fetched_exam:
            return {"exam_details": [], "fetch_exam_details": True}
        for rec in fetched_exam:
            exam_rec = request.env["xe.exam"].sudo().browse(rec["id"])
            rec.update(
                {
                    "term_id": exam_rec.session_id.academic_term_id.id,
                    "term_name": exam_rec.session_id.academic_term_id.name,
                }
            )
        return {
            "exam_details": fetched_exam,
            "Attendees": request.env["xe.exam.attendees"]
            .sudo()
            .search_read(
                [("id", "in", fetched_exam[0]["attendees_line_ids"])],
                ["id", "student_id", "exam_id", "status", "marks", "comments"],
            ),
        }

    @http.route("/v1/web/dataset/reset/draft/exams/details", type="json", auth="user")
    def reset_draft_exam_details(self, exam_id):
        if not request.env.user.has_group("xe_exam_management.group_xe_exam_admin"):
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User do not allowed/access to do current operation",
                }
            }
        try:
            fetched_exam = request.env["xe.exam"].sudo().browse(int(exam_id))

            if not fetched_exam:
                return {"exam_details": [], "fetch_exam_details": True}
            if fetched_exam.state == "held":
                fetched_exam.act_draft()
            else:
                return {
                    "status": "exam is not in held status so it can't be setted "
                    "as draft or it's already in draft"
                }
            if fetched_exam.state == "draft":
                return {"status": "exam setted to draft state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route("/v1/web/dataset/held/draft/exams/details", type="json", auth="user")
    def held_draft_exam_details(self, exam_id):
        if not request.env.user.has_group("xe_exam_management.group_xe_exam_admin"):
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User do not allowed/access to do current operation",
                }
            }
        try:
            fetched_exam = request.env["xe.exam"].sudo().browse(int(exam_id))

            if not fetched_exam:
                return {"exam_details": [], "fetch_exam_details": True}
            if fetched_exam.state == "draft":
                fetched_exam.action_held_exam()
            else:
                return {
                    "status": "exam is not in draft status so it can't be setted "
                    "as held or it's already in held"
                }
            if fetched_exam.state == "held":
                return {"status": "exam setted to held state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/v1/web/dataset/update/result/exams/attendees/details",
        type="json",
        auth="user",
    )
    def update_result_exam_attendeed_details(self, args):
        try:
            for rec in args:
                fetched_attendeed_line = (
                    request.env["xe.exam.attendees"]
                    .sudo()
                    .browse(int(rec["attendees_line_id"]))
                )

                if not fetched_attendeed_line:
                    return {
                        "exam_details": "Exam attendees not found",
                        "fetch_exam_attendees_details": True,
                    }
                if fetched_attendeed_line.exam_id.state == "held":
                    fetched_attendeed_line.sudo().write({"marks": rec["marks"]})

                else:
                    return {
                        "status": "exam is not in held status so it can't be update result"
                    }
            return {"status": "exam result updated"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route("/v1/web/dataset/update/result/exams/details", type="json", auth="user")
    def update_result_exam_details(self, exam_id):
        try:
            fetched_exam = request.env["xe.exam"].sudo().browse(int(exam_id))

            if not fetched_exam:
                return {"exam_details": "Exam id not found", "fetch_exam_details": True}
            if fetched_exam.state == "held":
                fetched_exam.sudo().act_result_updated()
            else:
                return {
                    "status": "exam is not in held status so it can't be update result"
                }
            if fetched_exam.state == "result_updated":
                return {"status": "exam result updated"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route("/v1/web/dataset/reset/held/exams/details", type="json", auth="user")
    def reset_held_exam_details(self, exam_id):
        if not request.env.user.has_group("xe_exam_management.group_xe_exam_admin"):
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User do not allowed/access to do current operation",
                }
            }
        try:
            fetched_exam = request.env["xe.exam"].sudo().browse(int(exam_id))

            if not fetched_exam:
                return {"exam_details": [], "fetch_exam_details": True}
            if fetched_exam.state in ("result_updated", "done"):
                fetched_exam.act_held()
            else:
                return {
                    "status": "exam is must be in result updated or done so it can't be "
                    "setted as held or it's already in held"
                }
            if fetched_exam.state == "held":
                return {"status": "exam setted to held state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route("/v1/web/dataset/done/exams/details", type="json", auth="user")
    def set_done_exam_details(self, exam_id):
        try:
            fetched_exam = request.env["xe.exam"].sudo().browse(int(exam_id))

            if not fetched_exam:
                return {"exam_details": [], "fetch_exam_details": True}
            if fetched_exam.state == "result_updated":
                fetched_exam.sudo().act_done()
            else:
                return {
                    "status": "exam is not in result updated state so it can't be"
                    " setted as Done or it's already in Done"
                }
            if fetched_exam.state == "done":
                return {"status": "exam setted to done state"}
        except Exception as e:
            return {"result": {"message": "Failed", "flag": False, "error": str(e)}}

    @http.route(
        "/v1/web/dataset/fetch/marksheet_line/details", type="json", auth="user"
    )
    def fetch_marksheet_details(self, marksheet_line_id):
        user_type = self.get_user_type()
        if user_type["school_access"] in ["student"]:
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User not allowed to do current xeeration",
                }
            }
        fetched_marksheet_line = (
            request.env["xe.marksheet.line"]
            .sudo()
            .search_read([("id", "=", marksheet_line_id)])
        )
        if not fetched_marksheet_line:
            return {"marksheet_line_details": [], "fetch_marksheet_line": True}
        return {
            "marksheet_line_details": fetched_marksheet_line,
            "result_line": request.env["xe.result.line"]
            .sudo()
            .search_read(
                [("id", "in", fetched_marksheet_line[0]["result_line"])],
                ["id", "student_id", "exam_id", "marks", "status", "comments"],
            ),
        }

    @http.route(
        "/v1/web/dataset/fetch/exams/details/for/teacher", type="json", auth="user"
    )
    def fetch_exam_details_for_teacher(self, **kw):
        offset, limit = set_offset_limit(kw)
        fields = [
            "name",
            "company_id",
            "session_id",
            "course_id",
            "subject_id",
            "state",
            "exam_code",
            "attendees_line_ids"
        ]
        exam_admin_access = request.env.user.has_group(
            "xe_exam_management.group_xe_exam_admin"
        )
        exam_user_access = request.env.user.has_group(
            "xe_exam_management.group_xe_exam_user"
        )
        if not exam_admin_access and not exam_user_access:
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User do not allowed/access to do current operation",
                }
            }

        domain = []
        if exam_user_access:
            domain = [("staff_id", "=", int(kw["teacher_id"]))]
            if kw.get("session_id", False):
                domain = [("staff_id", "=", int(kw["teacher_id"])), ("session_id", "=", kw["session_id"])]
        if exam_admin_access:
            if kw.get("session_id", False):
                domain = [("session_id", "=", kw["session_id"])]

        fetched_exam = request.env["xe.exam"].sudo().search_read(domain, fields, offset=offset, limit=limit)

        if not fetched_exam:
            return {"exam_details": [], "fetch_exam_details": True}
        attendes_list = []
        for rec in fetched_exam:
            attendes = (
                request.env["xe.exam.attendees"]
                .sudo()
                .search_read(
                    [("id", "in", rec["attendees_line_ids"])],
                    [
                        "id",
                        "student_id",
                        "exam_id",
                        "status",
                        "marks",
                        "comments",
                    ],
                )
            )
            attendes_list.append(
                {"exam_id": rec["id"], "exam_name": rec["name"], "attendes": attendes}
            )
        for rec in fetched_exam:
            exam_rec = request.env["xe.exam"].sudo().browse(rec["id"])
            rec.update(
                {
                    "term_id": [exam_rec.session_id.academic_term_id.id, exam_rec.session_id.academic_term_id.name]
                }
            )
        return {
            "exam_details": fetched_exam,
            "Attendees": attendes_list
        }

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
        d = {}
        for key, val in values:
            if key in d:
                d[key] += val
            else:
                d[key] = val
        list_new = [(k, v) for k, v in d.items()]
        return list_new

    def compute_class_position(self, student_id, exam_session_id):
        rank = 1
        student_id = student_id or False
        position_array = []

        marksheet_register = request.env["xe.marksheet.register"].search(
            [("exam_session_id", "=", exam_session_id)]
        )
        same_obj = marksheet_register.marksheet_line
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

    @http.route("/v1/web/dataset/exam/dashboard/fetch", type="json", auth="user")
    def fetch_session_dashboard_counts(self, student_id, exam_session_id):
        result = {}
        domain = []
        if not student_id or not exam_session_id:
            return result
        if student_id:
            domain.append(("student_id", "=", student_id))
        marksheet_lines = request.env["xe.marksheet.line"].sudo().search(domain)
        total_obtained = sum([line.total_marks for line in marksheet_lines])
        total_percentage = sum([line.percentage for line in marksheet_lines])
        c_position, c_length = self.compute_class_position(student_id, exam_session_id)
        class_post_str = str(c_position) + " out of " + str(c_length)

        result["total_students_class"] = c_length
        result["total_obtained"] = total_obtained
        result["total_percentage"] = total_percentage
        result["class_position"] = c_position
        result["class_position_str"] = class_post_str
        student_result_line = {}
        for mark_sheet in marksheet_lines:
            for line in mark_sheet.result_line:
                if line.exam_id.name not in student_result_line:
                    student_result_line[line.exam_id.name] = {
                        "exam_name": line.exam_id.name,
                        "subject_name": line.exam_id.subject_id.name,
                        "student_marks": line.marks,
                    }
                else:
                    student_result_line[line.exam_id.name]["student_marks"] = (
                        student_result_line[line.exam_id.name]["student_marks"]
                        + line.marks
                    )
        if exam_session_id:
            domain.append(("exam_session_id", "=", exam_session_id))
            session = request.env["xe.exam.session"].browse(exam_session_id)
            total_marks = sum([line.total_marks for line in session.exam_ids])
            result["total_marks"] = total_marks
            for exam in session.exam_ids:
                result_lines = request.env["xe.result.line"].search(
                    [("exam_id", "=", exam.id)]
                )
                avg_marks = 0
                if result_lines:
                    avg_marks = sum([line.marks for line in result_lines]) / len(
                        result_lines
                    )
                student_result_line[exam.name]["class_avg"] = avg_marks
        result["student_result_line"] = list(student_result_line.values())

        return result

    @http.route("/v1/web/dataset/fetch/exam_sessions/details", type="json", auth="user")
    def fetch_exam_session_details(self, exam_session_id):
        user_type = self.get_user_type()
        if user_type["school_access"] in ["student", "parent"]:
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User not allowed to do current xeeration",
                }
            }
        exam_session = (
            request.env["xe.exam.session"]
            .sudo()
            .search_read([("id", "=", exam_session_id)])
        )
        if not exam_session:
            return {"exam_sessions": [], "fetch_exam_session": True}
        return {
            "exam_sessions": exam_session,
            "exam_ids": request.env["xe.exam"]
            .sudo()
            .search_read(
                [("id", "in", exam_session[0]["exam_ids"])],
                [
                    "id",
                    "name",
                    "subject_id",
                    "exam_code",
                    "start_time",
                    "end_time",
                    "state",
                    "total_marks",
                    "min_marks",
                ],
            ),
        }

    @http.route(
        "/v1/web/dataset/fetch/marksheet_line/student/details", type="json", auth="user"
    )
    def fetch_marsksheet_details_student(self, student_id):
        user_type = self.get_user_type()
        if user_type["school_access"] in ["student"]:
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User not allowed to do current xeeration/operation",
                }
            }
        marksheet_line_ids = (
            request.env["xe.marksheet.line"]
            .sudo()
            .search_read([("student_id", "=", int(student_id))])
        )
        marksheet_data = []
        for line in marksheet_line_ids:
            result_line = (
                request.env["xe.result.line"]
                .sudo()
                .search_read(
                    [("id", "in", line["result_line"])],
                    ["id", "student_id", "exam_id", "marks", "status", "comments"],
                )
            )
            marksheet_data.append({"marksheet_line": line, "result_line": result_line})
        if not marksheet_line_ids:
            return {
                "result": {"fetch_marksheet": True, "marksheet_lines": "No data found"}
            }
        return {"marksheet_lines": marksheet_data}

    @http.route(
        "/v1/web/dataset/fetch/marksheet_line/parent/details", type="json", auth="user"
    )
    def fetch_marsksheet_details_parent(self, partner_id):
        user_type = self.get_user_type()
        if user_type["school_access"] in ["student"]:
            return {
                "result": {
                    "message": "Failed",
                    "flag": False,
                    "error": "User not allowed to do current xeeration",
                }
            }
        user_id = (
            request.env["res.users"]
            .sudo()
            .search([("partner_id", "=", int(partner_id))])
        )
        if not user_id:
            return {
                "student_ids": [],
                "fetch_students": False,
                "note": "There is no parent found related to partner",
            }
        xe_parent_id = (
            request.env["xe.parent"].sudo().search([("user_id", "=", user_id.id)])
        )
        student_ids = (
            request.env["xe.student"]
            .sudo()
            .search_read([("id", "in", xe_parent_id.student_ids.ids)])
        )
        marksheet_data = []
        for rec in xe_parent_id.student_ids:
            marksheet_line_ids = (
                request.env["xe.marksheet.line"]
                .sudo()
                .search_read([("student_id", "=", rec.id)])
            )
            for line in marksheet_line_ids:
                result_line = (
                    request.env["xe.result.line"]
                    .sudo()
                    .search_read(
                        [("id", "in", line["result_line"])],
                        ["id", "student_id", "exam_id", "marks", "status", "comments"],
                    )
                )
                marksheet_data.append(
                    {
                        "student_id": rec["id"],
                        "marksheet_line": line,
                        "result_line": result_line,
                    }
                )

        if not student_ids:
            return {"student_ids": [], "fetch_students": True}
        return {"student_ids": student_ids, "marksheet_lines": marksheet_data}

    @http.route("/exam/student/marksheetlines", type="json", auth="user")
    def get_exam_student_marksheetlines(self, **kw):
        student_data = []
        student = (
            request.env["xe.student"]
            .sudo()
            .search([("partner_id", "=", int(kw["partner_id"]))], limit=1)
        )
        offset, limit = set_offset_limit(kw)
        if student:
            marksheet_lines = self.get_marksheetlines(student, offset, limit)
            student_data.append(marksheet_lines)
        return student_data

    def get_marksheetlines(self, student_id, offset, limit):
        marksheet_lines = (
            request.env["xe.marksheet.line"]
            .sudo()
            .search_read(
                [("student_id", "=", student_id.id)],
                [
                    "exam_session_id",
                    "academic_term_id",
                    "total_marks",
                    "student_id",
                    "course_id",
                    "classroom_id",
                    "evaluation_type",
                    "academic_year_id",
                    "result_line_ids",
                    "head_master_comment",
                ],
                offset=offset,
                limit=limit,
            )
        )
        if marksheet_lines:
            for ml in marksheet_lines:
                result_lines = (
                    request.env["xe.result.line"]
                    .sudo()
                    .search_read(
                        [("id", "in", ml["result_line_ids"])],
                        [
                            "subject_id",
                            "marks",
                        ],
                    )
                )
                ml.update({"result_line_ids": result_lines})
        return marksheet_lines

    @http.route(
        "/exam/marksheetlines/844/marksheetline/download/<int:marksheetline_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_844_marksheetline_download(self, marksheetline_id):
        try:
            pdf = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf(
                    "xe_exam_management.report_marksheetline", [marksheetline_id]
                )[0]
            )
            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
            ]
            result = request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            result_dict = {
                "result": {
                    "message": "Failed",
                    "error": str(e),
                    "flag": False,
                }
            }
            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/exam/marksheetlines/844/combine_marksheetline/download/<int:marksheetline_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_844_combine_marksheetline_download(self, marksheetline_id):
        try:
            pdf = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf(
                    "xe_exam_management.report_combine_marksheetline",
                    [marksheetline_id],
                )[0]
            )
            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
            ]
            result = request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            result_dict = {
                "result": {
                    "message": "Failed",
                    "error": str(e),
                    "flag": False,
                }
            }
            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/exam/session", type="json", auth="user"
    )
    def get_exam_sessions(self, **kw):
        user_type = self.get_user_type()
        offset, limit = set_offset_limit(kw)
        domain = [("company_id", "=", user_type["company_id"])]
        if kw.get("searchby", False):
            domain += [
                "|",
                ("name", "ilike", kw["searchby"]),
                ("exam_code", "ilike", kw["searchby"])
            ]
        session_ids = (
            request.env["xe.exam.session"]
            .sudo()
            .search_read(domain, ['name', 'exam_code'], offset=offset, limit=limit, order="id desc")
        )
        return session_ids