from odoo import models, fields


class LostMedia(models.TransientModel):
    _name = "lost.media"
    _description = "Lost Media"

    reason = fields.Char(required=True)
    media_unit_id = fields.Many2one("xe.media.unit", required=True)

    def lost_media_action(self):
        for unit in self:
            value = {}
            if unit.media_unit_id.state:
                media_movement = self.env["xe.media.movement"].search(
                    [
                        ("media_unit_id", "=", unit.media_unit_id.id),
                        ("state", "=", "issue"),
                    ],
                    limit=1,
                )
                for movement in media_movement:
                    movement.write({"state": "lost"})

                unit.media_unit_id.state = "lost"
                media_state = self.env["xe.media.unit"].search(
                    [("id", "=", unit.media_unit_id.id)], limit=1
                )
                for media_unit in media_state:
                    media_unit.write({"reason": unit.reason})
                value = {"type": "ir.actions.act_window_close"}
