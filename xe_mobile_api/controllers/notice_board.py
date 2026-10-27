""" Notice board APIs python file """
# pylint: disable= E0401, C0116
from datetime import datetime
from odoo import http
from odoo.http import request
from ..controllers.main import set_offset_limit

NOTICE_BOARD_FIELDS = [
    "name",
    "sequence",
    "desc",
    "active",
    "create_date",
    "company_id",
    "website_id",
]


class NoticeBoard(http.Controller):
    """Notice board APIs"""

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

    @http.route("/notice_board/details", auth="user", type="json")
    def get_notice_board_details(self, date):
        user_type = self.get_user_type()
        nb = (
            request.env["sh.nb.notice.board"]
            .sudo()
            .search([('company_id', '=', user_type.get("company_id"))], order="sequence asc")
            .filtered(
                lambda l: l.create_date.date()
                == datetime.strptime(date, "%Y-%m-%d").date()
                and l.active
            )
        )
        if nb:
            nb_ids = (
                request.env["sh.nb.notice.board"]
                .sudo()
                .search_read(
                    [("id", "in", nb.ids)],
                    NOTICE_BOARD_FIELDS,
                )
            )
            return nb_ids
        date_split = date.split("-")
        date_formatting = date_split[2] + "/" + date_split[1] + "/" + date_split[0]
        return [
            {
                "message": "There are no entries found in the Notice Board for %s"
                % (date_formatting)
            }
        ]

    @http.route("/notice_board/searchby", auth="user", type="json")
    def get_notice_board_searchby(self, **kw):
        user_type = self.get_user_type()
        offset, limit = set_offset_limit(kw)
        nb = (
            request.env["sh.nb.notice.board"]
            .sudo()
            .search([('company_id', '=', user_type.get("company_id"))], offset=offset, limit=limit, order="sequence asc")
            .filtered(
                lambda l: l.create_date.date()
                == datetime.strptime(kw["date"], "%Y-%m-%d").date()
                and l.active
            )
        )
        if nb:
            nb_ids = (
                request.env["sh.nb.notice.board"]
                .sudo()
                .search_read(
                    [
                        ("id", "in", nb.ids),
                        "|",
                        ("name", "ilike", kw["searchby"]),
                        ("desc", "ilike", kw["searchby"]),
                    ],
                    NOTICE_BOARD_FIELDS,
                )
            )
            if nb_ids:
                return nb_ids
        return [
            {
                "message": "There are no entries found in the Notice Board for %s"
                % (kw["searchby"])
            }
        ]
