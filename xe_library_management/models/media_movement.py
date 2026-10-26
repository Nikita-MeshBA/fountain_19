# -*- coding: utf-8 -*-

from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo import models, fields, api


class MediaRenew(models.Model):
    _name = "xe.media.renew"
    _description = "Media Renew"

    movement_id = fields.Many2one("xe.media.movement", "Media Movement")
    renew_date = fields.Date()
    librarian_id = fields.Many2one("res.users")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )


class OpMediaMovement(models.Model):
    _inherit = "xe.media.movement"

    @api.depends("media_id", "media_id.queue_ids")
    def _compute_media_count(self):
        for media in self:
            count = 0
            if media.media_id and media.media_id.queue_ids:
                count = len(media.media_id.queue_ids)
            media.queue_count = count

    queue_count = fields.Float("Media Queue Count", compute="_compute_media_count")
    media_movement_id = fields.Many2one("xe.media.movement", "Parent Media Movement")
    is_renew = fields.Boolean("Renew")
    renew_ids = fields.One2many("xe.media.renew", "movement_id", "Renew Details")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    def action_renew_media(self):
        self.actual_return_date = fields.Date.today()
        self.calculate_penalty()
        if self.penalty:
            raise UserError(_("Can't renew media \n you have penalty to pay"))
        date = relativedelta(days=self.library_card_id.library_card_type_id.duration)

        self.env["xe.media.renew"].create(
            {
                "librarian_id": self.env.user.id,
                "movement_id": self.id,
                "renew_date": fields.Date.today(),
            }
        )
        self.return_date = datetime.today() + date
        self.is_renew = True

        return True
