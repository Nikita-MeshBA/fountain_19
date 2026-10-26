from datetime import timedelta

from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _


class RenewMedia(models.TransientModel):
    """Renew Media Wizard"""

    _name = "renew.media"
    _description = "renew.media"

    media_id = fields.Many2one("xe.media")
    media_unit_id = fields.Many2one("xe.media.unit")
    issue_date = fields.Date()
    actual_return_date = fields.Date()
    move_due_date = fields.Date("Return Date")
    renew_issue_date = fields.Date()
    renew_return_date = fields.Date()

    @api.constrains("renew_issue_date", "renew_return_date")
    def _check_date(self):
        if self.renew_issue_date > self.renew_return_date:
            raise ValidationError(
                _("Renew Return Date cannot be set before Renew Issued Date.")
            )

    @api.onchange("renew_issue_date")
    def _onchange_renew_issue_date(self):
        if self.renew_issue_date:
            duration = self.media_unit_id.movement_lines_ids[
                -1
            ].library_card_id.library_card_type_id.duration
            self.renew_return_date = self.renew_issue_date + timedelta(days=duration)

    def check_max_issue(self, student_id, library_card_id):
        media_movement_search = self.env["xe.media.movement"].search(
            [
                ("library_card_id", "=", library_card_id),
                ("student_id", "=", student_id),
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

    def do_renew(self):
        for media in self:
            value = {}
            movement_line_id = self.media_unit_id.movement_lines_ids[-1]
            movement_line_id.state = "renew"
            if self.check_max_issue(
                movement_line_id.student_id.id, movement_line_id.library_card_id.id
            ):
                new_movement_id = movement_line_id.copy()
                new_movement_id.write(
                    {
                        "issued_date": media.renew_issue_date,
                        "return_date": media.renew_return_date,
                        "actual_return_date": False,
                        "state": "issue",
                    }
                )
                value = {"type": "ir.actions.act_window_close"}
            else:
                raise UserError(
                    _(
                        f"Maximum Number of media allowed for {movement_line_id.student_id.name} "
                        f"is : {movement_line_id.library_card_id.library_card_type_id.allow_media}"
                    )
                )
            return value
