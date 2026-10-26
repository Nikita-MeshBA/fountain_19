# -*- coding: utf-8 -*-


from datetime import timedelta, date

from odoo import fields, http, _
from odoo.http import request


class EventBarcode(http.Controller):
    @http.route("/xe_library_barcode/register_attendee", type="jsonrpc", auth="user")
    def register_attendee(self, barcode, media_barcode, librarycard_barcode, **kw):
        media_unit_number = media_barcode
        library_card_number = librarycard_barcode
        unit = request.env["op.media.unit"].search(
            [("barcode", "=", media_unit_number)]
        )
        card = request.env["op.library.card"].search(
            [("number", "=", library_card_number)]
        )
        faculty_id = card.type == "faculty" and card.faculty_id.id or False
        student_id = card.type == "student" and card.student_id.id or False
        media_movement_search = request.env["op.media.movement"].search(
            [
                ("library_card_id", "=", card.id),
                ("student_id", "=", card.student_id.id),
                ("state", "=", "issue"),
            ]
        )
        if len(media_movement_search) < card.library_card_type_id.allow_media:
            if unit.state and unit.state == "available":
                media_movement_create = {
                    "media_id": unit.media_id.id,
                    "media_unit_id": unit.id,
                    "type": card.type,
                    "student_id": student_id,
                    "faculty_id": faculty_id,
                    "library_card_id": card.id,
                    "issued_date": fields.Date.today(),
                    "return_date": date.today()
                    + timedelta(days=card.library_card_type_id.duration),
                    "state": "available",
                }
                movement = request.env["op.media.movement"].create(
                    media_movement_create
                )
                movement.issue_media()
            else:
                return {
                    "warning": f"Media Unit can not be issued because it's state is : {unit.state}"
                }
        else:
            return {
                "warning": f"Maximum Number of media allowed for {card.student_id.name} is : {card.library_card_type_id.allow_media}"
            }
        return {"success": _("Successfully Issue")}

    @http.route("/xe_library_barcode/return_media", type="jsonrpc", auth="user")
    def return_media(self, barcode, **kw):
        media_unit_number = barcode
        unit = request.env["op.media.unit"].search(
            [("barcode", "=", media_unit_number)]
        )
        media_move_search = request.env["op.media.movement"].search(
            [("media_unit_id", "=", unit.id), ("state", "=", "issue")]
        )
        if not media_move_search:
            return {"warning": f"Can't return media : {media_unit_number}"}
        media_move_search.return_media(date.today())
        return {
            "success": _("Successfully Return"),
            "penalty": media_move_search.penalty or 0.0,
        }
