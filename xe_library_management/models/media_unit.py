# -*- coding: utf-8 -*-

from datetime import date, timedelta

from odoo import models, fields, api


class OpMediaUnit(models.Model):
    _name = "xe.media.unit"
    _inherit = "mail.thread"
    _description = "Media Unit"
    _rec_name = "barcode"
    _rec_names_search = ["name", "barcode"]

    name = fields.Char()
    media_id = fields.Many2one("xe.media", required=True, tracking=True)
    barcode = fields.Char("Media Code", size=20)
    movement_lines_ids = fields.One2many(
        "xe.media.movement", "media_unit_id", "Movements"
    )
    state = fields.Selection(
        [("available", "Available"), ("issue", "Issued"), ("lost", "Lost")],
        default="available",
        tracking=True,
    )
    media_type_id = fields.Many2one(related="media_id.media_type_id", store=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    media_isbn = fields.Char(related="media_id.isbn")
    media_internal_code = fields.Char(related="media_id.internal_code")
    media_edition = fields.Char(related="media_id.edition")
    media_tags_ids = fields.Many2many(related="media_id.tags_ids")
    media_author_ids = fields.Many2many(related="media_id.author_ids")
    media_publisher_ids = fields.Many2many(related="media_id.publisher_ids")
    reason = fields.Char(tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("media_id"):
                media_obj = self.env["xe.media"].browse(vals.get("media_id"))
                sequence_code = media_obj.media_type_id.sequence_id.code
                vals["barcode"] = self.env["ir.sequence"].next_by_code(sequence_code)
        return super(OpMediaUnit, self).create(vals_list)

    def renew_media_action(self):
        duration = self.movement_lines_ids[
            -1
        ].library_card_id.library_card_type_id.duration
        return {
            "name": ("Renew Media"),
            "view_mode": "form",
            "res_model": "renew.media",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {
                "default_issue_date": (
                    self.movement_lines_ids[-1].issued_date
                    if self.movement_lines_ids[-1].issued_date
                    else False
                ),
                "default_move_due_date": (
                    self.movement_lines_ids[-1].return_date
                    if self.movement_lines_ids[-1].return_date
                    else False
                ),
                "default_actual_return_date": (
                    self.movement_lines_ids[-1].actual_return_date
                    if self.movement_lines_ids[-1].actual_return_date
                    else False
                ),
                "default_renew_issue_date": date.today(),
                "default_renew_return_date": date.today() + timedelta(days=duration),
                "default_media_unit_id": self.id,
            },
        }
