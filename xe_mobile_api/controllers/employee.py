""" Employee APIs python file """
# pylint: disable= E0401, C0116, W0718
import io
import json
import math
import base64
from datetime import datetime
from odoo.http import request, Response, content_disposition
from odoo import http


class EmployeeApi(http.Controller):
    """Employee APIs"""

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

    def get_number_of_days(self, date_from, date_to, employee_id):
        """Returns a float equals to the timedelta between two dates given as string."""
        from_dt = date_from
        to_dt = date_to

        if employee_id:
            employee = request.env["hr.employee"].browse(employee_id)
            work_days_data = employee._get_work_days_data_batch(date_from, date_to)
            return work_days_data[employee.id]["days"]

        time_delta = to_dt - from_dt
        return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)

    def get_employee_user_type(self):
        hr_user = request.env.user.has_group("hr.group_hr_user")
        hr_manager = request.env.user.has_group("hr.group_hr_manager")
        access_role = "employee"
        if hr_user:
            access_role = "hr_user"
        if hr_manager:
            access_role = "hr_manager"
        return access_role

    @http.route("/v1/web/fetch/employee-leaves", type="json", auth="user")
    def employee_leave_history(self, employee_id):
        search_flag = False
        result = {"message": "Failed", "error": "Authentication Failed", "flag": False}
        hr_user = request.env.user.has_group("hr.group_hr_holidays_user")
        hr_manager = request.env.user.has_group("hr.group_hr_holidays_manager")
        if hr_user or hr_manager:
            search_flag = True
        if not search_flag:
            emp_obj = request.env["hr.employee"].sudo().browse(employee_id)
            if emp_obj.user_id.id == request.env.user.id:
                search_flag = True
        if search_flag:
            fields = [
                "id",
                "name",
                "holiday_status_id",
                "date_from",
                "date_to",
                "number_of_days",
                "supported_attachment_ids",
                "state",
            ]
            leaves = (
                request.env["hr.leave"]
                .sudo()
                .search_read(
                    [
                        ("employee_id", "=", employee_id),
                    ],
                    fields,
                )
            )
            for leave in leaves:
                leave_obj = request.env["hr.leave"].sudo().browse(leave["id"])
                new_state = dict(
                    leave_obj.fields_get(allfields=["state"])["state"]["selection"]
                )[leave_obj.state]
                leave["state"] = new_state
                attachment_ids = []
                for att_obj in leave["supported_attachment_ids"]:
                    attachments = request.env["ir.attachment"].search_read(
                        [("id", "=", att_obj)],
                        ["id", "name", "mimetype", "file_size", "checksum"],
                    )
                    attachment_ids.append(attachments)
                leave["attachment_ids"] = attachment_ids
            result = leaves
        return result

    @http.route("/v1/web/fetch/employee-leave_types", type="json", auth="user")
    def employee_remaining_leave(self, employee_id):
        search_flag = False
        result = {"message": "Failed", "error": "Authentication Failed", "flag": False}
        hr_user = request.env.user.has_group("hr.group_hr_holidays_user")
        hr_manager = request.env.user.has_group("hr.group_hr_holidays_manager")
        if hr_user or hr_manager:
            search_flag = True
        if not search_flag:
            emp_obj = request.env["hr.employee"].sudo().browse(employee_id)
            if emp_obj.user_id.id == request.env.user.id:
                search_flag = True
        if search_flag:
            fields = ["id", "name"]
            total_leaves = 0
            result = {}
            leave_types = request.env["hr.leave.type"].sudo().search_read([], fields)
            for l_type in leave_types:
                holiday_status_id = l_type["id"]
                leave_alloc = (
                    request.env["hr.leave.allocation"]
                    .sudo()
                    .search(
                        [
                            ("employee_id", "=", employee_id),
                            ("holiday_status_id", "=", holiday_status_id),
                            ("state", "=", "validate"),
                        ]
                    )
                )
                alloc_days = 0
                if leave_alloc:
                    alloc_days = sum(leave_alloc.mapped("number_of_days"))
                leave_s = (
                    request.env["hr.leave"]
                    .sudo()
                    .search(
                        [
                            ("employee_id", "=", employee_id),
                            ("holiday_status_id", "=", holiday_status_id),
                            ("state", "not in", ["cancel", "refuse"]),
                        ]
                    )
                )
                leaves_taken = 0
                if leave_s:
                    leaves_taken = sum(leave_s.mapped("number_of_days"))
                remaining_leaves = alloc_days - leaves_taken
                l_type["remaining_leaves"] = remaining_leaves
                total_leaves += remaining_leaves
            result["total_remaining_leaves"] = total_leaves
            result["leave_types"] = leave_types
        return result

    @http.route("/v1/web/fetch/employee-payslip", type="json", auth="user")
    def employee_payslips(self, employee_id):
        payslips = {
            "message": "Failed",
            "error": "Authentication Failed",
            "flag": False,
        }
        res = self.get_employee_user_type()
        search_flag = False
        if res == "employee":
            emp_obj = request.env["hr.employee"].sudo().browse(employee_id)
            if emp_obj.user_id.id == request.env.user.id:
                search_flag = True
        if res in ["hr_user", "hr_manager"]:
            search_flag = True
        if search_flag:
            fields = ["id", "name", "date_from", "date_to"]
            domain = [("state", "=", "done")]
            if employee_id:
                domain.append(("employee_id", "=", employee_id))
            payslips = request.env["hr.payslip"].sudo().search_read(domain, fields)
        return payslips

    @http.route(
        "/v1/web/fetch/employee/payslip/<int:payslip_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_payslip(self, payslip_id):
        result_dict = {
            "result": {
                "message": "Failed",
                "flag": False,
            }
        }
        pdfhttpheaders = [
            ("Content-Type", "application/json"),
        ]
        try:
            payslip = request.env["hr.payslip"].sudo().browse(payslip_id)
            if payslip.state == "done":
                pdf = (
                    request.env["ir.actions.report"]
                    .sudo()
                    ._render_qweb_pdf(
                        "hr_payroll_community.action_report_payslip", [payslip_id]
                    )[0]
                )
                pdfhttpheaders = [
                    ("Content-Type", "application/pdf"),
                    ("Content-Length", len(pdf)),
                ]
                result = request.make_response(pdf, headers=pdfhttpheaders)
            else:
                result_dict["error"] = "Only Done Payslips can be downloaded"
                result = request.make_response(
                    json.dumps(result_dict), headers=pdfhttpheaders
                )
        except Exception as e:
            result_dict["error"] = str(e)
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route("/v1/web/fetch/employee-attendance", type="json", auth="user")
    def employee_attendance(self, employee_id):
        res = self.get_employee_user_type()
        search_flag = False
        if res == "employee":
            emp_obj = request.env["hr.employee"].sudo().browse(employee_id)
            if emp_obj.user_id.id == request.env.user.id:
                search_flag = True
        if res in ["hr_user", "hr_manager"]:
            search_flag = True
        if search_flag:
            fields = ["id", "check_in", "check_out"]
            domain = []
            if employee_id:
                domain.append(("employee_id", "=", employee_id))
            attendance_info = (
                request.env["hr.attendance"].sudo().search_read(domain, fields)
            )
        return attendance_info

    @http.route("/v1/web/fetch/faculty", type="json", auth="user")
    def fetch_faculties(self):
        return (
            request.env["hr.employee"]
            .sudo()
            .search_read(
                [("teach_type", "=", "teaching")],
                ["id", "name", "work_email", "company_id"],
            )
        )

    def fetch_employee(self):
        return (
            request.env["hr.employee"]
            .sudo()
            .search([("name", "=", request.env.user.name)], limit=1)
        )

    @http.route("/v1/web/fetch/employee/image", type="http", auth="user")
    def fetch_employee_image(self):
        # Search for the employee based on the currently logged-in user's name
        employee_record = self.fetch_employee()

        if not employee_record:
            return Response("Employee not found", status=404)

        image_data = employee_record.image_1920

        if not image_data:
            return Response("No image found for employee", status=404)
        data = io.BytesIO(base64.standard_b64decode(image_data))
        return http.send_file(data, filename=employee_record.name, as_attachment=True)

    @http.route("/v1/web/fetch/employee-info", type="json", auth="user")
    def employee_private_info(self):
        fields = [
            "name",
            "employee_no",
            "mobile_phone",
            "work_phone",
            "joining_date",
            "department_id",
            "job_id",
            "blood_group",
            "gender",
            "birthday",
            "identification_id",
            "pin_no",
            "nssf_no",
            "nhif_no",
            "nita_no",
            "bic_id",
            "debit_account_id",
            "id",
            "passport_id",
            "bank_account_id",
            "branch_code",
            "marital",
            "children",
            "visa_no",
            "work_email",
            "permit_no",
            "visa_expire",
            "qualification",
            "tsc_no",
            "place_of_birth",
            "company_id",
        ]
        employee_info = (
            request.env["hr.employee"]
            .sudo()
            .search_read([("name", "=", request.env.user.name)], fields)
        )
        if employee_info:
            return employee_info[0]
        return employee_info

    @http.route(
        "/v1/web/fetch/employee/p9report/<string:year>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_p9_report(self, year):
        result_dict = {
            "result": {
                "message": "Failed",
                "flag": False,
            }
        }
        pdfhttpheaders = [
            ("Content-Type", "application/json"),
        ]
        try:
            employee_record = self.fetch_employee()

            data = {
                "employee_id": employee_record,
                "year": year,
            }
            wizard_id = (
                request.env["p9.report.wizard"]
                .sudo()
                .create({"employee_id": employee_record.id, "year": year})
            )
            exel_content = (
                request.env["ir.actions.report"]
                .sudo()
                ._render(
                    "xe_kenya_hr_payroll.p9_xlsx_report",
                    [wizard_id.id],
                    data=data,
                )[0]
            )
            result = request.make_response(
                exel_content,
                headers=[
                    (
                        "Content-Type",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ),
                    (
                        "Content-Disposition",
                        content_disposition(
                            employee_record.name + " " + "P9report.xlsx"
                        ),
                    ),
                ],
            )
        except Exception as e:
            result_dict["error"] = str(e)
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/employee/payslip/<int:payslip_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_payslip_download(self, payslip_id):
        result_dict = {
            "result": {
                "message": "Failed",
                "flag": False,
            }
        }
        pdfhttpheaders = [
            ("Content-Type", "application/json"),
        ]
        try:
            payslip = request.env["hr.payslip"].sudo().browse(payslip_id)
            if payslip.state == "done":
                pdf = (
                    request.env["ir.actions.report"]
                    .sudo()
                    ._render_qweb_pdf(
                        "hr_payroll_community.action_report_payslip", [payslip_id]
                    )[0]
                )
                pdfhttpheaders = [
                    ("Content-Type", "application/pdf"),
                    ("Content-Length", len(pdf)),
                ]
                result = request.make_response(pdf, headers=pdfhttpheaders)
            else:
                result_dict["error"] = "Only Done Payslips can be downloaded"
                result = request.make_response(
                    json.dumps(result_dict), headers=pdfhttpheaders
                )
        except Exception as e:
            result_dict["error"] = str(e)
            result = request.make_response(
                json.dumps(result_dict), headers=pdfhttpheaders
            )
        return result

    @http.route(
        "/v1/web/fetch/employee/payslips/details",
        type="json",
        auth="user",
    )
    def get_employee_payslip_month_year(self, **kw):
        try:
            employee_record = self.fetch_employee()

            if "year" not in kw or "month" not in kw:
                return {"Failure": "Year and Month Require"}
            payslips = (
                request.env["hr.payslip"]
                .sudo()
                .search([("employee_id", "=", employee_record.id)])
            )
            filtered_payslips = payslips.filtered(
                lambda p: datetime.strptime(
                    p.date_from.strftime("%Y-%m-%d"), "%Y-%m-%d"
                ).month
                == kw["month"]
                and datetime.strptime(p.date_from.strftime("%Y-%m-%d"), "%Y-%m-%d").year
                == kw["year"]
            )
            if not filtered_payslips:
                return {"Failure": "No report found for search criteria entered."}
            data = (
                request.env["hr.payslip"]
                .sudo()
                .search_read([("id", "in", filtered_payslips.ids)])
            )
            return {"payslips": data}
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

    @http.route("/v1/web/fetch/leave-types", type="json", auth="user")
    def leave_types(self):
        fields = ["id", "name", "company_id"]
        leave_types = request.env["hr.leave.type"].sudo().search_read([], fields)
        return leave_types

    @http.route("/v1/web/create/employee-leaves", type="json", auth="user")
    def apply_leave(
        self, employee_id, holiday_status_id, date_from, date_to, description
    ):
        create_flag = False
        result = {"message": "Failed", "error": "Authentication Failed", "flag": False}
        hr_user = request.env.user.has_group("hr.group_hr_holidays_user")
        hr_manager = request.env.user.has_group("hr.group_hr_holidays_manager")
        if hr_user or hr_manager:
            create_flag = True
        if not create_flag:
            emp_obj = request.env["hr.employee"].sudo().browse(employee_id)
            if emp_obj.user_id.id == request.env.user.id:
                create_flag = True
        if create_flag:
            values = {}
            values["employee_id"] = employee_id
            values["holiday_status_id"] = holiday_status_id
            values["name"] = description
            values["date_from"] = datetime.strptime(date_from, "%d/%m/%Y %H:%M:%S")
            values["date_to"] = datetime.strptime(date_to, "%d/%m/%Y %H:%M:%S")
            values["request_date_from"] = datetime.strptime(
                date_from, "%d/%m/%Y %H:%M:%S"
            )
            values["request_date_to"] = datetime.strptime(date_to, "%d/%m/%Y %H:%M:%S")
            values["number_of_days"] = self.get_number_of_days(
                values["date_from"], values["date_to"], employee_id
            )
            try:
                create_obj = request.env["hr.leave"].create(values)
                result = {"message": "Success", "id": create_obj.id, "flag": True}
            except Exception as e:
                result = {"message": "Failed", "error": str(e), "flag": False}
        return result

    @http.route("/employee/students", type="json", auth="user")
    def get_employee_students(self):
        user = self.get_user_type()
        student_data = []
        student_ids = []
        if user.get("school_access") == "teacher" and user.get("employee_id"):
            employee_id = (
                request.env["hr.employee"]
                .sudo()
                .search([("id", "=", user.get("employee_id"))])
            )
            if employee_id and employee_id.subjects_ids:
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

        if user.get("school_access") == "back_office_admin":
            student_ids = (
                request.env["xe.student"]
                .sudo()
                .search([("company_id", "=", user.get("company_id"))])
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
        return student_data
