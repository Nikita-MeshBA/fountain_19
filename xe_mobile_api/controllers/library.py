""" Libarary APIs python file """
# pylint: disable= E0401, R0801, C0116
from datetime import datetime, date, timedelta
from odoo import http
from odoo.http import request


class LibraryAPI(http.Controller):
    """Libarary APIs python file"""

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

    def set_offset_limit(self, kw):
        offset, limit = 0, 0
        if kw.get("offset", False):
            offset = kw.get("offset")
        if kw.get("limit", False):
            limit = kw.get("limit")
        return offset, limit

    @http.route("/library/student_faculty/media_movement", type="json", auth="user")
    def get_student_faculty_media_movement(self, **kw):
        vals = []
        offset, limit = self.set_offset_limit(kw)

        domain = [("state", "=", "issue")]
        if kw.get("student_id", False):
            domain += [("student_id", "=", kw.get("student_id"))]
        if kw.get("faculty_id", False):
            domain += [("faculty_id", "=", kw.get("faculty_id"))]
        media_movement_ids = (
            request.env["xe.media.movement"]
            .sudo()
            .search(
                domain=domain,
                offset=offset,
                limit=limit,
            )
        )
        for movement in media_movement_ids:
            vals.append(self.get_media_movement_val(movement))
        return vals

    @http.route("/library/library_cards", type="json", auth="user")
    def get_library_cards(self):
        library_card_ids = (
            request.env["xe.library.card"]
            .sudo()
            .search_read(
                [], ["number", "partner_id", "student_id", "faculty_id", "course_id"]
            )
        )
        for card in library_card_ids:
            card["classroom_id"] = False
            if card.get("student_id"):
                classroom_id = (
                    request.env["xe.student"]
                    .sudo()
                    .search_read(
                        [("id", "=", card.get("student_id")[0])], ["classroom_id"]
                    )
                )
                if classroom_id:
                    card["classroom_id"] = classroom_id[0]["classroom_id"]
        return library_card_ids

    @http.route("/library/media_units/search", type="json", auth="user")
    def get_student_faculty_media_units(self, **kw):
        vals = []
        domain = [
            "|",
            "|",
            "|",
            "|",
            ("media_id.name", "ilike", kw["searchby"]),
            ("media_id.isbn", "ilike", kw["searchby"]),
            ("media_id.author_ids", "ilike", kw["searchby"]),
            ("media_id.publisher_ids", "ilike", kw["searchby"]),
            ("media_unit_id.barcode", "ilike", kw["searchby"]),
        ]
        offset, limit = self.set_offset_limit(kw)

        media_movement_ids = (
            request.env["xe.media.movement"]
            .sudo()
            .search(
                domain=domain,
                offset=offset,
                limit=limit,
            )
        )
        for movement in media_movement_ids:
            vals.append(self.get_media_movement_val(movement))
        if vals:
            return vals
        if not vals:
            return {
                "error_message": "There are no media unit associated with the search "
                "criteria entered."
            }

    def get_media_movement_val(self, movement):
        return {
            "media_unit": movement.media_id.name,
            "media_code": movement.media_id.isbn,
            "barcode": movement.media_unit_id.barcode,
            "issued_date": movement.issued_date,
            "due_date": movement.return_date,
            "description": movement.media_id.description,
            "media_internal_code": movement.media_id.internal_code,
            "media_edition": movement.media_id.edition
            and movement.media_id.edition.mapped("name")
            or [],
            "media_author": movement.media_id.author_ids
            and movement.media_id.author_ids.mapped("name")
            or [],
            "media_publisher": movement.media_id.publisher_ids
            and movement.media_id.publisher_ids.mapped("name")
            or [],
            "media_tags": movement.media_id.tags_ids
            and movement.media_id.tags_ids.mapped("name")
            or [],
        }

    @http.route("/library/user/access_rights", type="json", auth="user")
    def get_user_access_rights(self, **kw):
        access_right = (
            request.env["res.users"]
            .browse(kw.get("user_id"))
            .has_group("xe_library_management.group_xe_library")
        )
        return access_right

    @http.route("/library/media", type="json", auth="user")
    def get_media(self, **kw):
        vals = []
        offset, limit = self.set_offset_limit(kw)

        media_ids = (
            request.env["xe.media"].sudo().search([], offset=offset, limit=limit)
        )
        for media in media_ids:
            vals.append(self.get_media_val(media))
        return vals

    @http.route("/library/media/search", type="json", auth="user")
    def get_media_search(self, **kw):
        vals = []
        domain = [
            "|",
            "|",
            "|",
            "|",
            ("name", "ilike", kw["searchby"]),
            ("isbn", "ilike", kw["searchby"]),
            ("author_ids", "ilike", kw["searchby"]),
            ("publisher_ids", "ilike", kw["searchby"]),
            ("internal_code", "ilike", kw["searchby"]),
        ]
        offset, limit = self.set_offset_limit(kw)

        media_ids = (
            request.env["xe.media"].sudo().search(domain, offset=offset, limit=limit)
        )
        for media in media_ids:
            vals.append(self.get_media_val(media))
        if vals:
            return vals
        if not vals:
            return {
                "error_message": "There are no media associated with the search criteria entered."
            }

    def get_media_val(self, media):
        available_media_units = (
            request.env["xe.media.unit"]
            .sudo()
            .search([("media_id", "=", media.id), ("state", "=", "available")])
        )
        issue_media_units = (
            request.env["xe.media.unit"]
            .sudo()
            .search([("media_id", "=", media.id), ("state", "=", "issue")])
        )
        return {
            "id": media.id,
            "name": media.name,
            "media_author": media.author_ids and media.author_ids.mapped("name") or [],
            "media_publisher": media.publisher_ids
            and media.publisher_ids.mapped("name")
            or [],
            "media_isbn": media.isbn,
            "media_internal_code": media.internal_code,
            "media_edition": media.edition and media.edition.mapped("name") or [],
            "media_tags": media.tags_ids and media.tags_ids.mapped("name") or [],
            "media_type": media.media_type_id and media.media_type_id.name,
            "description": media.description,
            "class": media.course_ids and media.course_ids.mapped("name") or [],
            "subjects": media.subject_ids and media.subject_ids.mapped("name") or [],
            "available_media_units": len(available_media_units),
            "issue_media_units": len(issue_media_units),
        }

    @http.route("/library/media_type", type="json", auth="user")
    def get_media_type(self):
        media_types = request.env["xe.media.type"].sudo().search_read([], ["name"])
        return media_types

    @http.route("/library/media/filter", type="json", auth="user")
    def get_media_filter(self, **kw):
        vals = []
        offset, limit = self.set_offset_limit(kw)

        media_ids = (
            request.env["xe.media"]
            .sudo()
            .search(
                [("media_type_id", "=", kw.get("filterby"))], offset=offset, limit=limit
            )
        )
        for media in media_ids:
            vals.append(self.get_media_val(media))
        if vals:
            return vals
        if not vals:
            return {
                "error_message": "There are no media associated with the filter criteria entered."
            }

    @http.route("/library/media_units", type="json", auth="user")
    def get_media_units(self, **kw):
        offset, limit = self.set_offset_limit(kw)

        media_unit_ids = (
            request.env["xe.media.unit"]
            .sudo()
            .search_read([], ["media_id"], offset=offset, limit=limit)
        )
        return media_unit_ids

    @http.route("/library/button/issue_media", type="json", auth="user")
    def button_issue_media(self, **kw):
        media_unit_id = request.env["xe.media.unit"].browse([kw.get("media_unit_id")])

        if media_unit_id.state == "available":
            return {
                "media_id": media_unit_id.media_id.id,
                "media_unit_id": media_unit_id.id,
                "issued_date": date.today().strftime("%Y-%m-%d"),
                "return_date": date.today().strftime("%Y-%m-%d"),
            }
        error_message = "Media unit can not be issued because it's state is : %s" % (
            media_unit_id.state.capitalize()
        )
        return {"error_message": error_message}

    @http.route("/library/button/return_media", type="json", auth="user")
    def button_return_media(self, **kw):
        media_unit_id = request.env["xe.media.unit"].browse([kw.get("media_unit_id")])

        if media_unit_id.state == "issue":
            media_move = request.env["xe.media.movement"].search(
                [("media_unit_id", "=", media_unit_id.id), ("state", "=", "issue")],
                order="id desc",
            )
            return_date = media_move.return_date
            return {
                "media_id": media_unit_id.media_id.id,
                "media_unit_id": media_unit_id.id,
                "return_date": return_date.strftime("%Y-%m-%d"),
                "actual_return_date": date.today().strftime("%Y-%m-%d"),
                "penalty": 0,
            }
        error_message = "Media unit can not be issued because it's state is : %s" % (
            media_unit_id.state.capitalize()
        )
        return {"error_message": error_message}

    @http.route("/library/button/renew_media", type="json", auth="user")
    def button_renew_media(self, **kw):
        media_unit_id = request.env["xe.media.unit"].browse([kw.get("media_unit_id")])

        if media_unit_id.state == "issue":
            last_movement_line = media_unit_id.movement_lines_ids[-1]
            duration = last_movement_line.library_card_id.library_card_type_id.duration
            return {
                "media_id": media_unit_id.media_id.id,
                "media_unit_id": media_unit_id.id,
                "issued_date": last_movement_line.issued_date
                and last_movement_line.issued_date.strftime("%Y-%m-%d")
                or False,
                "return_date": last_movement_line.return_date
                and last_movement_line.return_date.strftime("%Y-%m-%d")
                or False,
                "actual_return_date": last_movement_line.actual_return_date
                and last_movement_line.actual_return_date.strftime("%Y-%m-%d")
                or False,
                "renew_issue_date": date.today().strftime("%Y-%m-%d"),
                "renew_return_date": (date.today() + timedelta(days=duration)).strftime(
                    "%Y-%m-%d"
                ),
            }
        error_message = "Media unit can not be issued because it's state is : %s" % (
            media_unit_id.state.capitalize()
        )
        return {"error_message": error_message}

    @http.route("/library/button/issue_media_proceed", type="json", auth="user")
    def button_issue_media_proceed(self, **kw):
        student_id = kw.get("student_id", False)
        faculty_id = kw.get("faculty_id", False)
        library_card_id = kw.get("library_card_id", False)
        media_id = request.env["xe.media"].browse([kw.get("media_id")])
        media_unit_id = request.env["xe.media.unit"].browse([kw.get("media_unit_id")])
        media_type = kw.get("type", False)
        issued_date = datetime.strptime(kw.get("issued_date"), "%Y-%m-%d").date()
        return_date = datetime.strptime(kw.get("return_date"), "%Y-%m-%d").date()

        if (
            request.env["issue.media"]
            .sudo()
            .check_max_issue(student_id, faculty_id, library_card_id)
        ):
            if media_unit_id.state and media_unit_id.state == "available":
                media_movement_create = {
                    "media_id": media_id.id,
                    "media_unit_id": media_unit_id.id,
                    "type": media_type,
                    "student_id": student_id or False,
                    "faculty_id": faculty_id or False,
                    "library_card_id": library_card_id,
                    "issued_date": issued_date,
                    "return_date": return_date,
                    "state": "issue",
                }
                try:
                    movement_id = (
                        request.env["xe.media.movement"]
                        .sudo()
                        .create(media_movement_create)
                    )
                except Exception as e:
                    return {"error_message": e.pgerror}
                media_unit_id.state = "issue"
                return True
            else:
                error_message = (
                    "Media unit can not be issued because it's state is : %s"
                    % (media_unit_id.state.capitalize())
                )
                return {"error_message": error_message}
        else:
            error_message = "Maximum Number of media allowed for %s is : %s" % (
                student_id.name,
                library_card_id.library_card_type_id.allow_media,
            )
            return {"error_message": error_message}

    @http.route("/library/button/return_media_proceed", type="json", auth="user")
    def button_return_media_proceed(self, **kw):
        media_unit_id = request.env["xe.media.unit"].browse([kw.get("media_unit_id")])
        actual_return_date = datetime.strptime(
            kw.get("actual_return_date"), "%Y-%m-%d"
        ).date()
        penalty = kw.get("penalty")

        if media_unit_id.state and media_unit_id.state == "issue":
            media_movement_id = (
                request.env["xe.media.movement"]
                .sudo()
                .search(
                    [
                        ("media_unit_id", "=", media_unit_id.id),
                        ("state", "=", "issue"),
                    ]
                )
            )
            if not media_movement_id:
                error_message = "Can't return media."
                return {"error_message": error_message}
            if penalty:
                invoice = self.create_penalty_invoice(media_unit_id, penalty)
                if isinstance(invoice, str):
                    return {"error_message": invoice}
            media_movement_id.return_media(actual_return_date)
            return True
        else:
            error_message = (
                "Media Unit can not be returned because it's state is : %s "
                % (media_unit_id.state.capitalize())
            )
            return {"error_message": error_message}

    def create_penalty_invoice(self, media_unit_id, penalty):
        account_id = False
        unit = media_unit_id
        media_move = request.env["xe.media.movement"].search(
            [("media_unit_id", "=", unit.id), ("state", "=", "issue")]
        )
        card = media_move.library_card_id
        product = card.library_card_type_id.product_id
        if product.id:
            account_id = product.property_account_income_id.id
        if not account_id:
            account_id = product.categ_id.property_account_income_categ_id.id
        if not account_id:
            error_message = (
                "There is no income account defined for this product: %s. "
                "You may have to install a chart of account from Accounting app, settings menu."
                % (product.name)
            )
            return error_message
        invoice = request.env["account.move"].create(
            {
                "partner_id": media_move.student_id.partner_id.id,
                "move_type": "out_invoice",
                "invoice_date": date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "account_id": account_id,
                            "price_unit": penalty,
                            "quantity": 1.0,
                            "discount": 0.0,
                            "product_id": product.id,
                        },
                    )
                ],
            }
        )
        media_move.write({"invoice_id": invoice.id})
        return True

    @http.route("/library/button/renew_media_proceed", type="json", auth="user")
    def button_renew_media_proceed(self, **kw):
        media_unit_id = request.env["xe.media.unit"].browse([kw.get("media_unit_id")])
        renew_issue_date = (
            kw.get("renew_issue_date")
            and datetime.strptime(kw.get("renew_issue_date"), "%Y-%m-%d").date()
            or False
        )
        renew_return_date = (
            kw.get("renew_return_date")
            and datetime.strptime(kw.get("renew_return_date"), "%Y-%m-%d").date()
            or False
        )
        actual_return_date = (
            kw.get("actual_return_date")
            and datetime.strptime(kw.get("actual_return_date"), "%Y-%m-%d").date()
            or False
        )

        movement_line_id = media_unit_id.movement_lines_ids[-1]
        if request.env["renew.media"].check_max_issue(
            movement_line_id.student_id.id, movement_line_id.library_card_id.id
        ):
            movement_line_id.state = "renew"
            new_movement_id = movement_line_id.copy()
            new_movement_id.write(
                {
                    "issued_date": renew_issue_date,
                    "return_date": renew_return_date,
                    "actual_return_date": actual_return_date,
                    "state": "issue",
                }
            )
            return True
        else:
            error_message = "Maximum Number of media allowed for %s is : %s" % (
                movement_line_id.student_id.name,
                movement_line_id.library_card_id.library_card_type_id.allow_media,
            )
            return {"error_message": error_message}
