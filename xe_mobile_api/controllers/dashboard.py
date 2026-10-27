""" Dashboard APIs python file """
# pylint: disable= E0401, C0116, R0801
import json
from datetime import date, datetime
from odoo import http
from odoo.http import request


class DashboardApi(http.Controller):
    """Dashboard APIs"""

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

    def get_cash_bank_journals(self):
        journals_list = []
        current_company = request.env.user.company_id.id
        try:
            journals = request.env["account.journal"].search(
                [("company_id", "=", current_company), ("type", "in", ["bank", "cash"])]
            )
            [
                journals_list.append(
                    {
                        "id": journal.id,
                        "name": journal.name,
                        "type": journal.type,
                        "account_balance": json.loads(journal.kanban_dashboard)[
                            "account_balance"
                        ],
                        "latest_statement": json.loads(journal.kanban_dashboard)[
                            "last_balance"
                        ],
                    }
                )
                for journal in journals
            ]
        except:
            journals_list = []
        return {"account_journals": journals_list}

    def get_exapense_collections(self, year):
        # Compute days wise expense
        j_query = """SELECT EXTRACT(YEAR FROM amv.date) AS year ,SUM(aml.amount_residual),\
                    ac.payment_type FROM account_payment AS ac
                    JOIN account_move AS amv ON ac.move_id=amv.id
                    JOIN account_move_line AS aml on aml.payment_id = ac.id
                    LEFT JOIN account_journal as aj ON aj.id = amv.journal_id
                    WHERE amv.state IN ('posted', 'reconciled')AND 
                    EXTRACT(YEAR FROM amv.date) = %s
                    GROUP BY year,ac.payment_type order by year,ac.payment_type;"""
        request.cr.execute(j_query, (year,))
        result = request.cr.fetchall()
        total_expense = 0
        total_income = 0
        for line in result:
            if line[2] == "outbound":
                total_expense += line[1] * -1
            if line[2] == "inbound":
                total_income += line[1]
        return total_expense

    def get_fleet_costs(self):
        query = """select vehicle_id,name,sum(cost) as amt from fleet_vehicle_cost_report
         group by vehicle_id,name order by amt limit 5;"""
        request.cr.execute(query)
        result = request.cr.fetchall()
        fleet_s = []
        total_amt = 0
        for res in result:
            values = {}
            values["id"] = res[0]
            values["name"] = res[1]
            values["amount"] = res[2]
            total_amt += res[2]
            fleet_s.append(values)
        for fleet in fleet_s:
            percentage = 0
            if total_amt:
                percentage = (fleet["amount"] / total_amt) * 100
            fleet["percentage"] = percentage
        return fleet_s

    @http.route("/v1/web/fetch/dashboard/user/accounting", type="json", auth="user")
    def dashboard_accounting(self):
        user_id = request.env.user
        vals = {}
        if user_id.has_group(
            "xenesis_school_base.group_account_officer"
        ) or user_id.has_group("account.group_account_manager"):
            vals["journals"] = self.get_cash_bank_journals()
            vals["invoices"] = [0, 0]
            invoice_ids = request.env["account.move"].search(
                [
                    ("move_type", "=", "out_invoice"),
                    ("state", "!=", "cancel"),
                    ("payment_state", "!=", "paid"),
                ]
            )
            for inv in invoice_ids:
                vals["invoices"][0] += 1
                vals["invoices"][1] += inv.amount_residual

            vals["vendor_bills"] = [0, 0]
            vendor_bill_ids = request.env["account.move"].search(
                [
                    ("move_type", "=", "in_invoice"),
                    ("state", "!=", "cancel"),
                    ("payment_state", "!=", "paid"),
                ]
            )
            for vb in vendor_bill_ids:
                vals["vendor_bills"][0] += 1
                vals["vendor_bills"][1] += vb.amount_residual
        return vals

    @http.route("/v1/web/fetch/dashboard/teacher", type="json", auth="user")
    def dashboard_teacher(self):
        result = self.get_user_type()
        vals = {}
        if (
            result
            and result.get("school_access", False)
            and result.get("school_access") == "teacher"
        ):
            if request.env.user.employee_id:
                employee_id = request.env.user.employee_id
                if request.env.user.employee_id.teach_type == "teaching":
                    student_count = 0
                    if employee_id.subject_ids:
                        for classroom in employee_id.subject_ids.mapped(
                            "classroom_ids"
                        ):
                            student_ids = request.env["xe.student"].search(
                                [("classroom_id", "=", classroom.id)]
                            )
                            student_count += len(student_ids)
                    vals["student_count"] = student_count

                payslip_ids = request.env["hr.payslip"].search(
                    [("employee_id", "=", employee_id.id)]
                )
                payslip_count = 0
                for ps in payslip_ids:
                    if ps.date_from.year == date.today().year:
                        payslip_count += 1
                vals["payslip_count"] = payslip_count
            vals["employee_count"] = len(request.env["hr.employee"].search([]))
        return vals

    @http.route("/v1/web/fetch/dashboard/parent", type="json", auth="user")
    def dashboard_parent(self):
        result = self.get_user_type()
        vals = {}
        if result and result.get("parent_id", False):
            parent_id = request.env["xe.parent"].browse([result.get("parent_id")])
            vals["student_count"] = len(parent_id.student_ids)
            if len(parent_id.student_ids):
                vals["student_list"] = []
                for student_line in parent_id.student_ids:
                    student_id = request.env["xe.student"].search(
                        [("roll_number", "=", student_line.roll_number)], limit=1
                    )
                    attendance_ids = request.env["xe.attendance.details"].search(
                        [
                            ("student_id", "=", student_id.id),
                            ("attendance_date", "=", date.today()),
                        ]
                    )
                    invoice_ids = request.env["account.move"].search(
                        [
                            ("roll_number", "=", student_line.roll_number),
                            ("state", "=", "posted"),
                            ("payment_state", "=", "not_paid"),
                        ]
                    )
                    exam_marksheet_line_count = request.env["xe.marksheet.line"].search(
                        [
                            ("student_id", "=", student_id.id),
                            (
                                "marksheet_reg_id.exam_session_id.academic_year_id",
                                "=",
                                student_id.current_academic_year_id.id,
                            ),
                        ]
                    )
                    vals["student_list"].append(
                        {
                            "id": student_id.id,
                            "name": student_id.name,
                            "attendance_count": len(attendance_ids)
                            if attendance_ids
                            else 0,
                            "invoices_count": len(invoice_ids) if invoice_ids else 0,
                            "exam_marksheet_line_count": len(
                                exam_marksheet_line_count.mapped("result_line")
                            )
                            if exam_marksheet_line_count
                            else 0,
                        }
                    )
        return vals

    @http.route("/v1/web/dataset/school/dashboard/fetch", type="json", auth="user")
    def fetch_school_dashboard_counts(self, student_id):
        user_type = self.get_user_type()
        attendance_domain = []
        attendance_sheet_domain = []
        assignment_domain = []
        timetable_domain = [("state", "=", "confirm")]
        exam_sessions = []
        performance_list = []
        if user_type["school_access"] in ["student", "parent"] and student_id:
            student_obj = request.env["xe.student"].sudo().browse(student_id)
            attendance_domain.append(("student_id", "=", student_id))
            assignment_domain.append(("id", "in", student_obj.allocation_ids.ids))
            timetable_domain.append(
                ("course_id", "=", student_obj.course_detail_ids[0].course_id.id)
            )
            timetable_domain.append(
                ("batch_id", "=", student_obj.course_detail_ids[0].batch_id.id)
            )
            # Fetch Exam Session Details of Student(s)
            exam_attendees = (
                request.env["xe.exam.attendees"]
                .sudo()
                .search([("student_id", "=", student_id)])
            )
            exam_ids = []
            for line in exam_attendees:
                if line.exam_id not in exam_ids:
                    exam_ids.append(line.exam_id)
            exam_session_ids = []
            for line in exam_ids:
                if line.session_id not in exam_session_ids:
                    exam_session_ids.append(line.session_id)
            if exam_session_ids:
                for exam_session in exam_session_ids:
                    exam_sessions.append(exam_session.read(["id", "name"])[0])

            # Fetch session wise Performance of the student in the current year
            start_date = date(date.today().year, 1, 1)
            end_date = date(date.today().year, 12, 31)
            current_year_sessions = (
                request.env["xe.exam.session"]
                .sudo()
                .search(
                    [
                        "|",
                        ("end_date", ">", start_date),
                        ("end_date", "=", start_date),
                        "|",
                        ("end_date", "<", end_date),
                        ("end_date", "=", end_date),
                    ]
                )
            )
            for session in current_year_sessions:
                marksheet_register = (
                    request.env["xe.marksheet.register"]
                    .sudo()
                    .search(
                        [
                            ("exam_session_id", "=", session.id),
                            ("state", "=", "validated"),
                        ],
                        limit=1,
                    )
                )
                performance = {}
                if marksheet_register and student_id:
                    marksheet_line_ids = marksheet_register.marksheet_line_ids.filtered(
                        lambda d: d.student_id.id == student_id
                    )
                    if marksheet_line_ids:
                        performance["exam_session"] = session.name
                        performance["percentage"] = marksheet_line_ids.percentage
                if performance:
                    performance_list.append(performance)
        if user_type["school_access"] in ["teacher"]:
            teacher_obj = request.env["hr.employee"].search(
                [("partner_id", "=", request.env.user.partner_id.id)]
            )
            attendance_domain.append(
                ("attendance_id.teacher_user_id", "=", request.env.user.id)
            )
            assignment_domain.append(("create_teacher_id", "=", request.env.user.id))
            timetable_domain.append(("teacher_id", "=", teacher_obj.id))

        if user_type["school_access"] in ["back_office_admin"]:
            exam_sessions = request.env["xe.exam.session"].search_read(
                [], ["id", "name"]
            )

        # Fetch Attendance Details
        attendance_count = (
            request.env["xe.attendance.details"].sudo().search_count(attendance_domain)
        )

        #     Fetch Assignment Details
        assignments = request.env["xe.assignment"].sudo().search(assignment_domain)
        assignment_publish_count = len(
            assignments.filtered(lambda x: x.state == "assigned").ids
        )
        assignment_draft_count = len(
            assignments.filtered(lambda x: x.state == "draft").ids
        )
        assignment_finish_count = len(
            assignments.filtered(lambda x: x.state == "done").ids
        )

        # Fetch Timetable Data
        timetable_count = (
            request.env["xe.timetable.sessions"].sudo().search_count(timetable_domain)
        )

        # Fetch Attendance Details
        attendance_sheets = (
            request.env["xe.student.attendance"].sudo().search(attendance_sheet_domain)
        )
        attendance_sheet_draft = len(
            attendance_sheets.filtered(lambda a: a.state == "draft").ids
        )
        attendance_sheet_submit = len(
            attendance_sheets.filtered(lambda a: a.state == "submitted").ids
        )
        attendance_sheet_approve = len(
            attendance_sheets.filtered(lambda a: a.state == "approved").ids
        )
        attendance_sheet_cancel = len(
            attendance_sheets.filtered(lambda a: a.state == "cancel").ids
        )

        male_students = request.env["xe.student"].search_count(
            [("active", "=", True), ("gender", "=", "male")]
        )
        female_students = request.env["xe.student"].search_count(
            [("active", "=", True), ("gender", "=", "female")]
        )

        current_year_start = str(date(date.today().year, 1, 1))
        current_year_end = str(date(date.today().year, 12, 31))
        prev_year_start = str(date(date.today().year - 1, 1, 1))
        prev_year_end = str(date(date.today().year - 1, 12, 31))
        current_year_admissions = request.env["xe.application"].search_count(
            [
                "|",
                ("create_date", ">", current_year_start),
                ("create_date", "=", current_year_start),
                "|",
                ("create_date", "<", current_year_end),
                ("create_date", "=", current_year_end),
            ]
        )
        previous_year_admissions = request.env["xe.application"].search_count(
            [
                "|",
                ("create_date", ">", prev_year_start),
                ("create_date", "=", prev_year_start),
                "|",
                ("create_date", "<", prev_year_end),
                ("create_date", "=", prev_year_end),
            ]
        )
        five_year_list = [
            date.today().year,
            date.today().year - 1,
            date.today().year - 2,
            date.today().year - 3,
            date.today().year - 4,
        ]
        five_year_expense_list = []
        total_expense = 0
        for f_year in five_year_list:
            five_year_expense = {}
            five_year_expense["year"] = f_year
            expense = self.get_exapense_collections(f_year)
            five_year_expense["expense"] = expense
            total_expense += expense
            five_year_expense_list.append(five_year_expense)
        for ex_obj in five_year_expense_list:
            percentage = 0
            if total_expense:
                percentage = (ex_obj["expense"] / total_expense) * 100
            ex_obj["percentage"] = percentage
        result = {
            "attendance_count": attendance_count,
            "timetable_count": timetable_count,
            "assignment_draft_count": assignment_draft_count,
            "assignment_publish_count": assignment_publish_count,
            "assignment_finish_count": assignment_finish_count,
            "assignment_total": assignment_draft_count
            + assignment_publish_count
            + assignment_finish_count,
            "attendance_sheet_draft": attendance_sheet_draft,
            "attendance_sheet_submit": attendance_sheet_submit,
            "attendance_sheet_approve": attendance_sheet_approve,
            "attendance_sheet_cancel": attendance_sheet_cancel,
            "exam_sessions": exam_sessions,
            "performance_over_time": performance_list,
        }
        result.setdefault("total_male_student", male_students)
        result.setdefault("total_female_student", female_students)
        result.setdefault("total_admissions_cur_yr_val", current_year_admissions)
        result.setdefault("total_admissions_pre_yr_val", previous_year_admissions)
        result.setdefault("total_admissions_cur_yr_key", str(date.today().year))
        result.setdefault("total_admissions_pre_yr_key", str(date.today().year - 1))
        result.setdefault("five_year_list", five_year_list)
        result.setdefault("five_year_expense", five_year_expense_list)
        result.setdefault("currency", request.env.user.company_id.currency_id.symbol)
        result.update(self.get_cash_bank_journals())
        result.setdefault("fleet_costs", self.get_fleet_costs())
        return result

    @http.route("/parent/dashboard", type="json", auth="user")
    def parent_dashboard(self, **kw):
        result = self.get_user_type()
        vals = {"assignment_count": 0, "notice_board_count": 0, "total_fee_balance": 0}
        if result and result.get("parent_id", False):
            date = datetime.strptime(kw.get("date"), "%Y-%m-%d").date()
            parent_id = request.env["xe.parent"].browse([result.get("parent_id")])
            student_ids = parent_id.student_ids
            for student in student_ids:
                vals["total_fee_balance"] += (
                    student.partner_id and student.partner_id.total_balance_partner or 0
                )
                assignment_ids = (
                    request.env["xe.assignment"]
                    .sudo()
                    .search(
                        [
                            ("state", "=", "assigned"),
                            ("student_ids", "in", [student.id]),
                        ]
                    )
                    .filtered(lambda l: l.create_date.date() == date)
                )
                vals["assignment_count"] += len(assignment_ids)

            nb = (
                request.env["sh.nb.notice.board"]
                .sudo()
                .search([])
                .filtered(lambda l: l.create_date.date() == date)
            )
            vals["notice_board_count"] += len(nb)
        return vals

    @http.route("/teacher/dashboard", type="json", auth="user")
    def teacher_dashboard(self, **kw):
        user = self.get_user_type()
        if user and user.get("school_access") == "back_office_admin":
            result = self._get_dashboard_details(
                "admin",
                request.env.user.employee_id
                and request.env.user.employee_id.id
                or False,
                user.get("company_id"),
            )

        if user and user.get("school_access") == "teacher" and user.get("employee_id"):
            result = self._get_dashboard_details(
                "teacher", user.get("employee_id") or False, user.get("company_id")
            )
        return result

    def _get_dashboard_details(self, access_right, employee_id, company_id):
        current_date = date.today()
        current_date_str = datetime.strftime(current_date, "%Y-%m-%d")
        vals = {
            "attendance_rate": float(0),
            "exam_count": 0,
            "assignment_count": 0,
            "class_count": 0,
            "classroom_count": 0,
            "male_students": 0,
            "female_students": 0,
            "total_students": 0,
        }
        if employee_id:
            employee_id = request.env["hr.employee"].sudo().browse([employee_id])

            total_students = 0
            present_students = 0
            attendance_register_ids = (
                request.env["xe.attendance.register"]
                .sudo()
                .search([("allowed_teachers_ids", "in", [employee_id.id])])
            )
            if attendance_register_ids:
                attendance_sheet_ids = (
                    request.env["xe.student.attendance"]
                    .sudo()
                    .search(
                        [
                            (
                                "attendance_register_id",
                                "in",
                                attendance_register_ids.ids,
                            ),
                            ("state", "in", ["submitted", "approved"]),
                        ]
                    )
                    .filtered(lambda l: l.attendance_date == current_date)
                )
                for sheet in attendance_sheet_ids:
                    for line in sheet.attendance_details_ids:
                        total_students += 1
                        if line.attendance == "present":
                            present_students += 1
                if total_students and present_students:
                    attendance_percentage = (present_students / total_students) * 100
                    vals["attendance_rate"] = float(
                        "{:.2f}".format(attendance_percentage)
                    )

            exam_ids = (
                request.env["xe.exam"]
                .sudo()
                .search(
                    [
                        ("staff_id", "=", employee_id.id),
                        ("state", "not in", ["done", "cancel"]),
                    ]
                )
            )
            vals["exam_count"] = len(exam_ids)

            assignment_ids = (
                request.env["xe.assignment"]
                .sudo()
                .search(
                    [("teacher_id", "=", employee_id.id), ("state", "!=", "cancel")]
                )
                .filtered(lambda l: l.create_date.date() == current_date)
            )
            vals["assignment_count"] = len(assignment_ids)

            student_ids = []
            if access_right == "admin":
                vals["class_count"] = len(request.env["xe.course"].sudo().search([]))
                vals["classroom_count"] = len(
                    request.env["xe.classroom"].sudo().search([])
                )
                student_ids = (
                    request.env["xe.student"]
                    .sudo()
                    .search([("company_id", "=", company_id)])
                )

            if access_right == "teacher" and employee_id.subjects_ids:
                class_ids = employee_id.subjects_ids.mapped("course_id.id")
                classroom_ids = employee_id.subjects_ids.mapped("classroom_ids").ids
                vals["class_count"] = len(class_ids)
                vals["classroom_count"] = len(classroom_ids)
                student_ids = (
                    request.env["xe.student"]
                    .sudo()
                    .search(
                        [
                            ("classroom_id", "in", classroom_ids),
                            ("company_id", "=", company_id),
                        ]
                    )
                )

            for student in student_ids:
                vals["total_students"] += 1
                if student.gender == "male":
                    vals["male_students"] += 1
                if student.gender == "female":
                    vals["female_students"] += 1
        return vals
