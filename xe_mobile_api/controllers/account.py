""" Accounting APIs python file """
# pylint: disable= E0401, C0116, R0801
import json
import datetime
from odoo import http
from odoo.http import request
from ..controllers.main import set_offset_limit


INVOICE_FIELDS = [
    "id",
    "name",
    "partner_id",
    "invoice_date",
    "currency_id",
    "course_id",
    "class_room_id",
    "terms",
    "roll_number",
    "payment_state",
    "invoice_line_ids",
    "invoice_date_due",
    "invoice_payment_term_id",
    "amount_total_signed",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "amount_residual",
    "amount_residual_signed",
]

PAYMENT_FIELDS = [
    "id",
    "name",
    "amount",
    "date",
    "ref",
    "partner_id",
    "journal_id",
    "currency_id",
    "payment_state",
]


class AccountApi(http.Controller):
    """Accounting APIs"""

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
        return res

    @http.route("/v1/web/dataset/invoices/search_read", type="json", auth="user")
    def get_invoices_list(self, fields):
        result = self.get_user_type()
        domain = []
        is_admin = False
        partners = request.env["res.partner"].sudo()
        invoices = request.env["account.move"].sudo()
        if result.get("school_access") == "parent":
            parent = request.env["xe.parent"].browse(result["parent_id"])
            if parent:
                partners = parent.student_ids.mapped("partner_id")
        if result.get("school_access") == "student":
            student = request.env["xe.student"].browse(result["student_id"])
            if student:
                partners = student.partner_id

        if result.get("school_access") == "back_office_admin":
            is_admin = True

        if is_admin:
            return invoices.search_read([])
        domain += [
            ("partner_id", "in", partners.ids),
            ("move_type", "=", "out_invoice"),
            ("state", "in", ["draft", "posted", "cancel"]),
        ]
        return invoices.search_read(domain, fields)

    @http.route("/v1/web/fetch/invoice", type="json", auth="user")
    def get_invoice(self, invoice_id):
        invoices = request.env["account.move"].sudo().browse(int(invoice_id))
        invoices_list = []
        for inv in invoices:
            invoices_lines = request.env["account.move.line"].search_read(
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
                    "invoice_user_id",
                    "team_id",
                    "journal_id",
                    "amount_untaxed",
                    "amount_tax",
                    "amount_total",
                    "amount_residual_signed",
                ]
            )[0]
            inv_res["invoices_lines"] = invoices_lines
            invoices_list.append(inv_res)
        return invoices_list

    @http.route("/account/parent/students", type="json", auth="user")
    def get_account_parent_students(self):
        result = self.get_user_type()
        student_data = []
        if result.get("school_access") == "parent":
            parent = request.env["xe.parent"].browse(result["parent_id"])
            if parent:
                student_ids = parent.sudo().student_ids
                for student in student_ids:
                    vals = {
                        "student_id": student.id,
                        "student_name": student.name,
                        "partner_id": student.partner_id and student.partner_id.id,
                        "total_balance_partner": student.partner_id
                        and student.partner_id.total_balance_partner,
                    }
                    student_data.append(vals)

        if result.get("school_access") == "student":
            student = request.env["xe.student"].browse(result["student_id"])
            if student:
                vals = {
                    "student_id": student.id,
                    "student_name": student.name,
                    "partner_id": student.partner_id and student.partner_id.id,
                    "total_balance_partner": student.partner_id
                    and student.partner_id.total_balance_partner,
                }
                student_data.append(vals)
        return student_data

    @http.route("/account/student/invoices", type="json", auth="user")
    def get_student_invoices(self, **kw):
        domain = [
            ("partner_id", "=", kw["partner_id"]),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
        ]
        offset, limit = set_offset_limit(kw)
        invoices = self.get_invoices(domain, offset, limit)
        if invoices:
            return invoices
        return [
            {
                "message": "There is no invoice associated with this profile;"
                " please contact the school admin."
            }
        ]

    @http.route("/account/invoices/groupby", type="json", auth="user")
    def get_invoices_groupby(self, partner_id, groupby_field):
        domain = [
            ("partner_id", "=", partner_id),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
        ]
        if groupby_field in ["day", "month", "year"]:
            groupby_field = "invoice_date:" + groupby_field
        invoices = (
            request.env["account.move"]
            .sudo()
            .read_group(domain, INVOICE_FIELDS, groupby=[groupby_field])
        )
        if invoices:
            return invoices
        return [
            {
                "message": "There are no invoices associated with the search criteria entered."
            }
        ]

    @http.route("/account/invoices/groupby_domain", type="json", auth="user")
    def get_invoices_groupby_domain(self, **kw):
        offset, limit = set_offset_limit(kw)
        invoices = self.get_invoices(kw["domain"], offset, limit)
        return invoices

    def get_year_range(self, year_str):
        today = datetime.date.today()
        if year_str == "this_year":
            year = today.year
        elif year_str == "last_year":
            year = today.year - 1
        else:
            raise ValueError(
                "Invalid year string. Please use 'this_year' or 'last_year'."
            )

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        return start_date, end_date

    @http.route("/account/invoices/filterby", type="json", auth="user")
    def get_invoices_filterby(self, **kw):
        domain = [
            ("partner_id", "=", kw["partner_id"]),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
        ]
        if "filterby_field" in kw:
            if kw["filterby_field"] == "paid":
                domain += [("payment_state", "in", ["in_payment", "paid"])]
            if kw["filterby_field"] == "not_paid":
                domain += [("payment_state", "in", ["partial", "not_paid"])]
        if "year" in kw:
            start_date, end_date = self.get_year_range(kw["year"])
            domain += [
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", end_date),
            ]

        offset, limit = set_offset_limit(kw)
        invoices = self.get_invoices(domain, offset, limit)
        if invoices:
            return invoices
        return [
            {
                "message": "There are no invoices associated with the search criteria entered."
            }
        ]

    @http.route("/account/invoices/searchby", type="json", auth="user")
    def get_invoices_searchby(self, **kw):
        domain = [
            ("partner_id", "=", kw["partner_id"]),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            "|",
            "|",
            ("name", "ilike", kw["searchby"]),
            ("partner_id.name", "ilike", kw["searchby"]),
            ("roll_number", "ilike", kw["searchby"]),
        ]
        offset, limit = set_offset_limit(kw)
        invoices = self.get_invoices(domain, offset, limit)
        if invoices:
            return invoices
        return [
            {
                "message": "There are no invoices associated with the search criteria entered."
            }
        ]

    def get_invoices(self, domain, offset, limit):
        invoices = (
            request.env["account.move"]
            .sudo()
            .search_read(domain, INVOICE_FIELDS, offset=offset, limit=limit)
        )

        if invoices:
            for invoice in invoices:
                invoice_lines = (
                    request.env["account.move.line"]
                    .sudo()
                    .search_read(
                        [("id", "in", invoice["invoice_line_ids"])],
                        [
                            "product_id",
                            "discount",
                            "discount_amount_currency",
                            "discount_fixed",
                            "price_subtotal",
                        ],
                    )
                )
                invoice.update({"invoice_line_ids": invoice_lines})
            return invoices
        return []

    @http.route(
        "/account/invoice/download/<int:invoice_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_invoice_download(self, invoice_id):
        try:
            pdf = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf("account.account_invoices", [invoice_id])[0]
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

    @http.route("/account/student/payments", type="json", auth="user")
    def get_student_payments(self, **kw):
        domain = [
            ("partner_id", "=", kw["partner_id"]),
            ("partner_type", "=", "customer"),
            ("state", "=", "posted"),
        ]
        offset, limit = set_offset_limit(kw)
        payments = (
            request.env["account.payment"]
            .sudo()
            .search_read(domain, PAYMENT_FIELDS, offset=offset, limit=limit)
        )
        if payments:
            return payments
        return [
            {
                "message": "There is no payment associated with this profile; "
                "please contact the school admin."
            }
        ]

    @http.route("/account/payments/groupby", type="json", auth="user")
    def get_payments_groupby(self, **kw):
        domain = [
            ("partner_id", "=", kw.get('partner_id')),
            ("partner_type", "=", "customer"),
            ("state", "=", "posted"),
        ]
        if kw.get('groupby_field') in ["day", "month", "year"]:
            groupby_field = "date:" + kw.get('groupby_field')
        payments = (
            request.env["account.payment"]
            .sudo()
            .read_group(domain, PAYMENT_FIELDS, groupby=[groupby_field])
        )
        if payments:
            return payments
        return [
            {
                "message": "There are no payments associated with the search criteria entered."
            }
        ]

    @http.route("/account/payments/groupby_domain", type="json", auth="user")
    def get_payments_groupby_domain(self, **kw):
        offset, limit = set_offset_limit(kw)
        return self.get_payments(kw.get('domain'), offset, limit)

    @http.route("/account/payments/filterby", type="json", auth="user")
    def get_payments_filterby(self, **kw):
        start_date = kw.get('filterby') + "-01-01"
        end_date = kw.get('filterby') + "-12-31"
        domain = [
            ("partner_id", "=", kw.get('partner_id')),
            ("partner_type", "=", "customer"),
            ("state", "=", "posted"),
            ("date", ">=", start_date),
            ("date", "<=", end_date),
        ]
        offset, limit = set_offset_limit(kw)
        return self.get_payments(domain, offset, limit)

    @http.route("/account/payments/searchby", type="json", auth="user")
    def get_payments_searchby(self, **kw):
        domain = [
            ("partner_id", "=", kw.get('partner_id')),
            ("partner_type", "=", "customer"),
            ("state", "=", "posted"),
            "|",
            "|",
            ("name", "ilike", kw.get('searchby')),
            ("partner_id.name", "ilike", kw.get('searchby')),
            ("ref", "ilike", kw.get('searchby')),
        ]
        offset, limit = set_offset_limit(kw)
        return self.get_payments(domain, offset, limit)

    def get_payments(self, domain, offset, limit):
        payments = (
            request.env["account.payment"].sudo().search_read(domain, PAYMENT_FIELDS, offset=offset, limit=limit)
        )
        if payments:
            return payments
        return [
            {
                "message": "There are no payments associated with the search criteria entered."
            }
        ]

    @http.route(
        "/account/payment/download/<int:payment_id>",
        type="http",
        auth="user",
        csrf=False,
    )
    def get_payment_download(self, payment_id):
        try:
            pdf = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf(
                    "account.action_report_payment_receipt", [payment_id]
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

    @http.route("/account/company/details", type="json", auth="user")
    def get_company_details(self):
        company_ids = (
            request.env["res.company"]
            .sudo()
            .search_read([], ["phone", "mobile", "email", "mpesa_paybill", "account"])
        )
        return company_ids
