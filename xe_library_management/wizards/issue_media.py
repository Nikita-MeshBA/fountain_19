# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _


class IssueMedia(models.TransientModel):
    """Issue Media"""

    _name = "issue.media"
    _description = "Issue Media"

    media_id = fields.Many2one("xe.media", required=True)
    media_unit_id = fields.Many2one("xe.media.unit", required=True)
    type = fields.Selection(
        [("student", "Student"), ("faculty", "Teacher")],
        default="student",
        required=True,
    )
    student_id = fields.Many2one("xe.student")
    # faculty_id = fields.Many2one('xe.staff', 'Teacher')
    faculty_id = fields.Many2one("hr.employee", "Teacher")
    library_card_id = fields.Many2one("xe.library.card", required=True)
    issued_date = fields.Date(required=True, default=fields.Date.today())
    return_date = fields.Date(required=True)

    @api.onchange("issued_date", "library_card_id")
    def _set_return_date(self):
        if self.issued_date and self.library_card_id:
            add_days = self.library_card_id.library_card_type_id.duration
            self.return_date = self.issued_date + timedelta(days=add_days)

    @api.constrains("issued_date", "return_date")
    def _check_date(self):
        if self.issued_date > self.return_date:
            raise ValidationError(_("Return Date cannot be set before Issued Date."))

    @api.onchange("library_card_id")
    def onchange_library_card_id(self):
        if self.library_card_id and self.library_card_id.type == "others":
            self.type = "faculty"
        else:
            self.type = self.library_card_id.type
        self.student_id = self.library_card_id.student_id.id
        self.faculty_id = self.library_card_id.faculty_id.id
        self.return_date = datetime.today() + relativedelta(
            days=self.library_card_id.library_card_type_id.duration
        )

    def check_max_issue(self, student_id, faculty_id, library_card_id):
        if student_id:
            media_movement_search = self.env["xe.media.movement"].search(
                [
                    ("library_card_id", "=", library_card_id),
                    ("student_id", "=", student_id),
                    ("state", "=", "issue"),
                ]
            )
        if faculty_id:
            media_movement_search = self.env["xe.media.movement"].search(
                [
                    ("library_card_id", "=", library_card_id),
                    ("faculty_id", "=", faculty_id),
                    ("state", "=", "issue"),
                ]
            )
        if (
            len(media_movement_search)
            < self.env["xe.library.card"]
            .browse(library_card_id)
            .library_card_type_id.allow_media
        ):
            return True
        else:
            return False

    def do_issue(self):
        for media in self:
            value = {}
            if media.check_max_issue(
                media.student_id.id or False,
                media.faculty_id.id or False,
                media.library_card_id.id,
            ):
                if (
                    media.media_unit_id.state
                    and media.media_unit_id.state == "available"
                ):
                    media_movement_create = {
                        "media_id": media.media_id.id,
                        "media_unit_id": media.media_unit_id.id,
                        "type": media.type,
                        "student_id": media.student_id.id or False,
                        "faculty_id": media.faculty_id.id or False,
                        "library_card_id": media.library_card_id.id,
                        "issued_date": media.issued_date,
                        "return_date": media.return_date,
                        "state": "issue",
                    }
                    self.env["xe.media.movement"].create(media_movement_create)
                    media.media_unit_id.state = "issue"
                    value = {"type": "ir.actions.act_window_close"}
                else:
                    # raise UserError(_("media Unit can not be issued \
                    # because it's state is : %s") % (dict(
                    #     media_unit.unit_states).get(media.media_unit_id.state)))
                    raise UserError(
                        _(
                            f"media Unit can not be issued because it's "
                            f"state is : {media.media_unit_id.state}"
                        )
                    )
            else:
                raise UserError(
                    _(
                        f"Maximum Number of media allowed for {media.student_id.name} "
                        f"is : {media.library_card_id.library_card_type_id.allow_media}"
                    )
                )
            return value
