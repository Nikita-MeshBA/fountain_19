""" Student APIs python file """
# pylint: disable= E0401, R0801, C0116, W0718, W0212
import json
import logging
from collections import OrderedDict
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import request
from odoo import http

_logger = logging.getLogger(__name__)


class XeStudentApi(http.Controller):
    """Student APIs"""

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
            res["employee_id"] = (
                request.env.user.employee_id
                and request.env.user.employee_id.id
                or False
            )
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

    @http.route("/v1/web/fetch/student", type="json", auth="user")
    def get_student_by_parent(self, parent_id):
        students = []
        parent = request.env["xe.parent"].sudo().search([("user_id", "=", parent_id)])
        for student in parent.student_ids:
            vals = {
                "name": student.name,
                "id": student.id,
                "email": student.email,
                "parent_id": parent_id,
                "company_id": student.company_id.id,
                "roll_number": student.roll_number,
                "nemis": student.nemis,
                "assessment_number": student.assessment_number,
                "gender": student.gender,
                "nationality_id": student.nationality_id.name,
                "blood_group": student.blood_group,
                "total_balance_partner": "{:.2f}".format(student.total_balance_partner),
                "dob": student.dob,
                "course_id": [student.course_id.id, student.course_id.name],
            }
            if student.classroom_id:
                vals["classroom_id"] = [
                    student.classroom_id.id,
                    student.classroom_id.name,
                ]
            else:
                vals["classroom_id"] = False
            if student.academic_year_id:
                vals["academic_year_id"] = [
                    student.academic_year_id.id,
                    student.academic_year_id.name,
                ]
            else:
                vals["academic_year_id"] = False
            if student.current_academic_year_id:
                vals["current_academic_year_id"] = [
                    student.current_academic_year_id.id,
                    student.current_academic_year_id.name,
                ]
            else:
                vals["current_academic_year_id"] = False
            students.append(vals)
        return students

    @http.route("/v1/web/fetch/student/invoices", type="json", auth="user")
    def get_student_invoice(self, student_id):
        student_id = request.env["xe.student"].sudo().browse(student_id)
        invoices = (
            request.env["account.move"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", student_id.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                ]
            )
        )
        invoices_list = []
        for inv in invoices:
            invoices_lines = (
                request.env["account.move.line"]
                .sudo()
                .search_read(
                    [("id", "in", inv.invoice_line_ids.ids)],
                    [
                        "id",
                        "product_id",
                        "name",
                        "account_id",
                        "quantity",
                        "product_uom_id",
                        "price_unit",
                        "discount",
                        "tax_ids",
                        "price_subtotal",
                    ],
                )
            )
            for line in invoices_lines:
                line["price_subtotal"] = "{:.2f}".format(line["price_subtotal"])
                line["price_unit"] = "{:.2f}".format(line["price_unit"])

            inv_res = inv.read(
                [
                    "id",
                    "name",
                    "partner_id",
                    "invoice_date_due",
                    "invoice_origin",
                    "amount_total_signed",
                    "state",
                    "roll_number",
                    "invoice_date",
                    "invoice_payment_term_id",
                    "currency_id",
                    "company_id",
                    "invoice_user_id",
                    "team_id",
                    "journal_id",
                    "amount_untaxed",
                    "amount_tax",
                    "amount_total",
                    "amount_residual_signed",
                    "terms",
                    "move_type",
                ]
            )[0]

            inv_res["amount_total"] = "{:.2f}".format(inv_res["amount_total"])
            inv_res["amount_residual_signed"] = "{:.2f}".format(
                inv_res["amount_residual_signed"]
            )
            inv_res["amount_total_signed"] = "{:.2f}".format(
                inv_res["amount_total_signed"]
            )
            inv_res["amount_untaxed"] = "{:.2f}".format(inv_res["amount_untaxed"])
            inv_res["amount_tax"] = "{:.2f}".format(inv_res["amount_tax"])
            inv_res["invoices_lines"] = invoices_lines
            inv_res["total_partner_balance"] = student_id.total_balance_partner
            inv_res["total_partner_balance"] = "{:.2f}".format(
                inv_res["total_partner_balance"]
            )
            inv_res["mpesa_paybill"] = inv.company_id.mpesa_paybill
            inv_res["account"] = inv.company_id.account
            inv_res["move_type"] = dict(
                inv.fields_get(allfields=["move_type"])["move_type"]["selection"]
            )[inv.move_type]
            invoices_list.append(inv_res)
        return invoices_list

    @http.route("/v1/web/fetch/student/attendance-lines", type="json", auth="user")
    def get_student_attendance_lines(self, student_id):
        result = []
        last_date = date.today() - relativedelta(months=6)
        month_list = OrderedDict(
            ((last_date + timedelta(_)).strftime(r"%m-%Y"), None)
            for _ in range((date.today() - last_date).days)
        ).keys()
        for month in month_list:
            attendance_data = {}
            attendance_line = []
            int_month = int(month.split("-")[0])
            int_year = int(month.split("-")[1])

            s_query = """select al.student_id,asht.attendance_date,\
            array_to_string(array_agg(al.attendance), ', ') from xe_attendance_details al 
            JOIN xe_student_attendance as asht on asht.id=al.attendance_id \
            and asht.state = 'approved' group by al.student_id,asht.attendance_date \
            having al.student_id=%s and EXTRACT('month' from asht.attendance_date) = %s 
            and EXTRACT('year' from asht.attendance_date) = %s;"""
            request.env.cr.execute(s_query, (student_id, int_month, int_year))
            result2 = request.env.cr.fetchall()
            total_present = 0
            total_absent = 0
            for res in result2:
                month_val = {}
                month_val["id"] = res[0]
                month_val["attendance_date"] = res[1]
                resp = list(str(res[2]))[0]
                if resp == "p":
                    month_val["present"] = True
                    month_val["attendance_status"] = "full_day"
                    total_present += 1
                else:
                    month_val["present"] = False
                    month_val["attendance_status"] = "absent"
                    total_absent += 1
                attendance_line.append(month_val)
            attendance_data["attendance_line"] = attendance_line
            attendance_data["total_present"] = total_present
            attendance_data["total_absent"] = total_absent
            vals = {"month_name": month, "attendance_data": attendance_data}
            result.append(vals)
        return result

    @http.route("/v1/web/fetch/student/exam-session", type="json", auth="user")
    def get_student_exam_session(self, student_id):
        res = self.get_user_type()
        session_fields = [
            "name",
            "exam_code",
            "start_date",
            "end_date",
            "course_id",
            # "term_id",
            "exam_type",
            "evaluation_type",
            "venue",
        ]
        if res["school_access"] in ["back_office_admin"]:
            session_list = []
            sessions = request.env["xe.exam.session"].sudo().search([])
            for session in sessions:
                session_vals = session.read(session_fields)[0]
                session_list.append(session_vals)
            return session_list
        else:
            domain = [("student_id", "=", student_id)]
            exam_attendees = request.env["xe.exam.attendees"].sudo().search(domain)
            exam_ids = []
            for line in exam_attendees:
                if line.exam_id not in exam_ids:
                    exam_ids.append(line.exam_id)
            exam_session_ids = []
            for line in exam_ids:
                if line.session_id not in exam_session_ids:
                    exam_session_ids.append(line.session_id)
            session_values = []
            if exam_session_ids:
                for e_session in exam_session_ids:
                    session_vals = e_session.read(session_fields)[0]
                    session_values.append(session_vals)
            return session_values

    @http.route("/v1/web/fetch/student/exams", type="json", auth="user")
    def get_student_exam(self, session_id):
        fields = [
            "id",
            "session_id",
            "name",
            "exam_code",
            "subject_id",
            "start_time",
            "end_time",
            "total_marks",
            "min_marks",
            "state",
        ]
        exam_ids = (
            request.env["xe.exam"]
            .sudo()
            .search([("session_id", "=", session_id), ("state", "in", ["done"])])
        )
        exams = exam_ids.read(fields)
        return exams

    @http.route("/v1/web/fetch/student/exam-result", type="json", auth="user")
    def get_student_exam_result(self, student_id):
        res = self.get_user_type()
        fields = ["id", "student_id", "exam_id", "marks", "comments", "status"]
        result = []
        marksheet_line_obj = False
        marksheet_fields = ["id", "status", "total_marks", "percentage"]
        if student_id and res["school_access"] in [
            "student",
            "parent",
            "back_office_admin",
        ]:
            marksheet_line_obj = (
                request.env["xe.marksheet.line"]
                .sudo()
                .search([("student_id", "=", student_id)])
            )
        if res["school_access"] in ["back_office_admin"] and not student_id:
            marksheet_line_obj = request.env["xe.marksheet.line"].sudo().search([])
        if marksheet_line_obj:
            for marksheet in marksheet_line_obj:
                marksheet_line = marksheet.read(marksheet_fields)[0]
                result_lines = (
                    request.env["xe.result.line"]
                    .sudo()
                    .search_read([("id", "in", marksheet.result_line.ids)], fields)
                )
                marksheet_line["result_lines"] = result_lines
                result.append(marksheet_line)
        return result

    @http.route("/v1/web/fetch/session/marksheet", type="json", auth="user")
    def get_session_exam_result(self, session_id, student_id):
        res = self.get_user_type()
        fields = ["id", "student_id", "exam_id", "marks", "comments", "status"]
        result = []
        marksheet_line_obj = False
        marksheet_fields = ["id", "status", "total_marks", "percentage"]
        domain = [("register_state", "=", "validated")]
        if session_id:
            domain.append(("exam_session_id", "=", session_id))
        if student_id:
            domain.append(("student_id", "=", student_id))
        if (
            session_id
            and student_id
            and res["school_access"] in ["student", "parent", "back_office_admin"]
        ):
            marksheet_line_obj = request.env["xe.marksheet.line"].sudo().search(domain)
        if marksheet_line_obj:
            for marksheet in marksheet_line_obj:
                marksheet_line = marksheet.read(marksheet_fields)[0]
                result_lines = (
                    request.env["xe.result.line"]
                    .sudo()
                    .search_read([("id", "in", marksheet.result_line.ids)], fields)
                )
                marksheet_line["result_lines"] = result_lines
                result.append(marksheet_line)
        return result

    @http.route(
        "/v1/web/fetch/student/hall-tickets/<int:session_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_student_hall_tickets(self, session_id):
        try:
            session_vals = request.env["xe.exam.session"].sudo().browse(session_id)
            data = {
                "id": session_id,
                "exam_session_id": [session_vals.id, session_vals.name],
            }
            pdf = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf(
                    "xe_exam_management.action_student_hall_ticket_report",
                    [session_id],
                    data=data,
                )[0]
            )
            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
            ]
            result = request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }

            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/student/mark-sheet-session/<int:exam_session_id>/<int:student_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_student_marksheet_session(self, exam_session_id, student_id):
        result = False
        try:
            res = self.get_user_type()
            mark_sheet_id = (
                request.env["xe.marksheet.register"]
                .search(
                    [
                        ("state", "=", "validated"),
                        ("exam_session_id", "=", exam_session_id),
                    ]
                )
                .id
            )
            if res["school_access"] in ["teacher", "back_office_admin"]:
                pdf = (
                    request.env["ir.actions.report"]
                    .sudo()
                    ._render_qweb_pdf(
                        "xe_exam_management.report_marksheet", [mark_sheet_id]
                    )[0]
                )
                pdfhttpheaders = [
                    ("Content-Type", "application/pdf"),
                    ("Content-Length", len(pdf)),
                ]
                result = request.make_response(pdf, headers=pdfhttpheaders)
            if res["school_access"] in ["student", "parent"]:
                marksheet_line_id = (
                    request.env["xe.marksheet.line"]
                    .sudo()
                    .search(
                        [
                            ("student_id", "=", student_id),
                            ("marksheet_reg_id", "=", mark_sheet_id),
                        ]
                    )
                )
                if marksheet_line_id:
                    sheet_line = marksheet_line_id.id
                    pdf = (
                        request.env["ir.actions.report"]
                        .sudo()
                        ._render_qweb_pdf(
                            "xe_exam_management.report_marksheetline", [sheet_line]
                        )[0]
                    )
                    pdfhttpheaders = [
                        ("Content-Type", "application/pdf"),
                        ("Content-Length", len(pdf)),
                    ]
                    result = request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }

            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/student/cbc-mark-sheet/<int:mark_sheet_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_student_cbc_marksheet(self, mark_sheet_id):
        try:
            get_param = request.env["ir.config_parameter"].sudo().get_param
            if get_param("xe_exam_management.group_rubrics_configurations"):
                pdf = (
                    request.env["ir.actions.report"]
                    .sudo()
                    ._render_qweb_pdf(
                        "xe_exam_management.report_cbc_marksheetline", [mark_sheet_id]
                    )[0]
                )
            elif get_param("xe_exam_management.group_subject_rubrics_configuration"):
                pdf = (
                    request.env["ir.actions.report"]
                    .sudo()
                    ._render_qweb_pdf(
                        "xe_exam_management.report_cbc_session_wise_marksheetline",
                        [mark_sheet_id],
                    )[0]
                )
            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
            ]
            fetched_marksheet_line = (
                request.env["xe.marksheet.line"].sudo().browse(mark_sheet_id)
            )
            if fetched_marksheet_line.evaluation_type == "1-3 CBC":
                result = request.make_response(pdf, headers=pdfhttpheaders)
            else:
                result_dict = {
                    "result": {
                        "message": "Marksheet Evaluation type is not CBC",
                        "flag": False,
                    }
                }

                pdfhttpheaders = [
                    ("Content-Type", "application/json"),
                ]
                result = request.make_response(
                    json.dumps(result_dict), headers=pdfhttpheaders
                )
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }

            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/student/cbc-combine-mark-sheet/<int:mark_sheet_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_student_cbc_combine_marksheet(self, mark_sheet_id):
        try:
            pdf = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf(
                    "xe_exam_management.report_cbc_combine_marksheetline",
                    [mark_sheet_id],
                )[0]
            )
            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
            ]
            fetched_marksheet_line = (
                request.env["xe.marksheet.line"].sudo().browse(mark_sheet_id)
            )
            if fetched_marksheet_line.evaluation_type == "1-3 CBC":
                result = request.make_response(pdf, headers=pdfhttpheaders)
            else:
                result_dict = {
                    "result": {
                        "message": "Marksheet Evaluation type is not CBC",
                        "flag": False,
                    }
                }

                pdfhttpheaders = [
                    ("Content-Type", "application/json"),
                ]
                result = request.make_response(
                    json.dumps(result_dict), headers=pdfhttpheaders
                )
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }

            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/student/combine-mark-sheet/<int:mark_sheet_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_student_combine_marksheet(self, mark_sheet_id):
        try:
            pdf = (
                request.env.ref("xe_exam_management.report_combine_marksheetline")
                .sudo()
                ._render_qweb_pdf([mark_sheet_id])[0]
            )
            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
            ]
            result = request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }

            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/student/mark-sheet/<int:mark_sheet_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_student_marksheet(self, mark_sheet_id):
        try:
            pdf = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf(
                    "xe_exam_management.report_marksheetline", [mark_sheet_id]
                )[0]
            )

            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
            ]
            result = request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }

            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/student/partner_id",
        type="json",
        auth="user",
        csrf=False,
    )
    def get_students(self):
        try:
            result = self.get_user_type()
            student_data = []
            if result.get("school_access") == "parent":
                parent = request.env["xe.parent"].browse(result["parent_id"])
                if parent:
                    student_ids = parent.sudo().student_ids
                    for student in student_ids:
                        vals = {
                            "student_id": student.id,
                            "student_partner_id": student.partner_id.id,
                        }
                        student_data.append(vals)

            if result.get("school_access") == "student":
                student = request.env["xe.student"].browse(result["student_id"])
                if student:
                    vals = {
                        "student_id": student.id,
                        "student_partner_id": student.partner_id.id,
                    }
                    student_data.append(vals)
            result = student_data
        except Exception as e:
            result_dict = {
                "result": {"message": "Failed", "flag": False, "error": str(e)}
            }

            pdfhttpheaders = [
                ("Content-Type", "application/json"),
            ]
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route("/parent/students", type="json", auth="user")
    def get_parent_students(self):
        result = self.get_user_type()
        student_data = []
        if result.get("school_access") == "parent":
            parent = request.env["xe.parent"].browse(result["parent_id"])
            if parent:
                student_ids = parent.sudo().student_ids
                for student in student_ids:
                    vals = {
                        "id": student.id,
                        "name": student.name,
                        "roll_number": student.roll_number,
                        "nationality": student.nationality_id
                        and student.nationality_id.name
                        or "",
                        "class_id": student.course_id and student.course_id.name or "",
                        "classroom_id": student.classroom_id
                        and student.classroom_id.name
                        or "",
                        "dob": student.dob or "",
                        "gender": student.gender
                        and dict(
                            request.env["xe.student"]._fields["gender"].selection
                        ).get(student.gender)
                        or "",
                        "joining_date": student.joined_date or "",
                        "blood_group": student.blood_group
                        and dict(
                            request.env["xe.student"]._fields["blood_group"].selection
                        ).get(student.blood_group)
                        or "",
                        "image": student.image_1920 or "",
                        "weekly_attendance_percentage": self.get_student_attendance_percentage(
                            student
                        ),
                    }
                    student_data.append(vals)

        if result.get("school_access") == "student":
            student = request.env["xe.student"].browse(result["student_id"])
            if student:
                vals = {
                    "id": student.id,
                    "name": student.name,
                    "roll_number": student.roll_number,
                    "nationality": student.nationality_id
                    and student.nationality_id.name
                    or "",
                    "class_id": student.course_id and student.course_id.name or "",
                    "classroom_id": student.classroom_id
                    and student.classroom_id.name
                    or "",
                    "dob": student.dob or "",
                    "gender": student.gender
                    and dict(request.env["xe.student"]._fields["gender"].selection).get(
                        student.gender
                    )
                    or "",
                    "joining_date": student.joined_date or "",
                    "blood_group": student.blood_group
                    and dict(
                        request.env["xe.student"]._fields["blood_group"].selection
                    ).get(student.blood_group)
                    or "",
                    "image": student.image_1920 or "",
                    "weekly_attendance_percentage": self.get_student_attendance_percentage(
                        student
                    ),
                }
                student_data.append(vals)
        return student_data

    def get_student_attendance_percentage(self, student):
        percentage = 0
        current_date = date.today()
        day_of_week = current_date.isocalendar()[2] - 1
        start_date = current_date - timedelta(days=day_of_week)
        dates = [start_date + timedelta(days=i) for i in range(7)]
        attendance_sheet_ids = (
            request.env["xe.student.attendance"]
            .sudo()
            .search([("state", "in", ["submitted", "approved"])])
            .filtered(
                lambda l: l.attendance_register_id.course_id.id == student.course_id.id
                and l.attendance_date in dates
            )
        )
        if attendance_sheet_ids:
            student_attendance = 0
            for att_sheet in attendance_sheet_ids:
                student_present_ids = att_sheet.attendance_details_ids.filtered(
                    lambda l: l.student_id.id == student.id
                    and l.attendance == "present"
                )
                student_attendance += len(student_present_ids)
            if student_attendance:
                percentage += (student_attendance / len(attendance_sheet_ids)) * 100
        return float("{:.2f}".format(percentage))

    @http.route("/students/groupby", type="json", auth="user")
    def students_groupby(self, **kw):
        data = []
        user = self.get_user_type()
        if user.get("school_access") == "teacher" and user.get("employee_id"):
            employee_id = (
                request.env["hr.employee"]
                .sudo()
                .search([("id", "=", user.get("employee_id"))])
            )
            if employee_id and employee_id.subjects_ids:
                class_ids = employee_id.subjects_ids.mapped("course_id.id")
                classroom_ids = employee_id.subjects_ids.mapped("classroom_ids").ids
                student_ids = (
                    request.env["xe.student"]
                    .sudo()
                    .search(
                        [
                            ("classroom_id", "in", classroom_ids),
                            ("company_id", "=", user.get("company_id")),
                        ]
                    )
                )

                if kw.get("groupby") == "class":
                    for class_id in class_ids:
                        cls_id = request.env["xe.course"].sudo().browse([class_id])
                        data.append(
                            {
                                "name": cls_id.name,
                                "student_count": len(
                                    student_ids.filtered(
                                        lambda l: l.course_id.id == class_id
                                    )
                                ),
                            }
                        )

                if kw.get("groupby") == "classroom":
                    for classroom_id in classroom_ids:
                        clsrm_id = (
                            request.env["xe.classroom"].sudo().browse([classroom_id])
                        )
                        data.append(
                            {
                                "name": clsrm_id.name,
                                "student_count": len(
                                    student_ids.filtered(
                                        lambda l: l.classroom_id.id == classroom_id
                                    )
                                ),
                            }
                        )

        if user.get("school_access") == "back_office_admin":
            if kw.get("groupby") == "class":
                course_ids = (
                    request.env["xe.student"]
                    .sudo()
                    .read_group(
                        [("company_id", "=", user.get("company_id"))],
                        [],
                        groupby=["course_id"],
                    )
                )
                for course in course_ids:
                    if course.get("course_id"):
                        data.append(
                            {
                                "name": course["course_id"][1],
                                "student_count": course["course_id_count"],
                            }
                        )
            if kw.get("groupby") == "classroom":
                classroom_ids = (
                    request.env["xe.student"]
                    .sudo()
                    .read_group(
                        [("company_id", "=", user.get("company_id"))],
                        [],
                        groupby=["classroom_id"],
                    )
                )
                for classroom in classroom_ids:
                    if classroom.get("classroom_id"):
                        data.append(
                            {
                                "name": classroom["classroom_id"][1],
                                "student_count": classroom["classroom_id_count"],
                            }
                        )
        return data

    @http.route("/student/searchby", type="json", auth="user")
    def get_student_searchby(self, **kw):
        student_data = []
        company_id = request.env.user.company_id.id
        domain = [
            ("company_id", "=", company_id),
            "|",
            ("name", "ilike", kw["searchby"]),
            ("roll_number", "ilike", kw["searchby"]),
        ]
        offset, limit = 0, 0
        if kw.get("offset", False):
            offset = kw["offset"]
        if kw.get("limit", False):
            limit = kw["limit"]

        student_ids = (
            request.env["xe.student"].sudo().search(domain, offset=offset, limit=limit)
        )
        for student in student_ids:
            vals = {
                "id": student.id,
                "name": student.name,
                "roll_number": student.roll_number,
                "class_id": student.course_id and student.course_id.name or "",
                "classroom_id": student.classroom_id
                and student.classroom_id.name
                or "",
                "gender": student.gender
                and dict(request.env["xe.student"]._fields["gender"].selection).get(
                    student.gender
                )
                or "",
            }
            student_data.append(vals)
        if student_data:
            return student_data
        return [{"message": "There are no student with the search criteria entered."}]
