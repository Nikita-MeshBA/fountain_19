# -*- coding: utf-8 -*-

from odoo.exceptions import UserError

from odoo import models, fields, api, _


class MediaPurchase(models.Model):
    _name = "xe.media.purchase"
    _inherit = "mail.thread"
    _description = "Media Purchase Request"

    name = fields.Char("Title", size=128, required=True)
    author = fields.Char("Author(s)", size=256, required=True, tracking=True)
    edition = fields.Char()
    publisher = fields.Char("Publisher(s)", size=256)
    course_ids = fields.Many2one("xe.course", "Class", required=True, tracking=True)
    # old field
    subject_ids = fields.Many2one("xe.subject", tracking=True)
    # new field
    subject_id = fields.Many2one("xe.subject", required=True, tracking=True)
    requested_id = fields.Many2one(
        "res.partner", "Requested By", default=lambda self: self.env.user.partner_id.id
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("request", "Requested"),
            ("reject", "Rejected"),
            ("accept", "Accepted"),
        ],
        readonly=True,
        default="draft",
        tracking=True,
    )
    media_type_id = fields.Many2one("xe.media.type")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    def action_request(self):
        self.state = "request"

    def action_accept(self):
        self.state = "accept"

    def action_reject(self):
        self.state = "reject"

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.child_ids:
            raise UserError(
                _("Invalid Action!\n Parent can not create Media Purchase Requests!")
            )
        return super(MediaPurchase, self).create(vals_list)

    def write(self, vals):
        if self.env.user.child_ids:
            raise UserError(
                _("Invalid Action!\n Parent can not edit Media Purchase Requests!")
            )
        return super(MediaPurchase, self).write(vals)
