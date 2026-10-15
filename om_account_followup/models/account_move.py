# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    followup_line_id = fields.Many2one("followup.line", "Follow-up Level")
    followup_date = fields.Date("Latest Follow-up")
    result = fields.Float(compute="_compute_get_result", string="Balance Amount")
    blocked = fields.Boolean(
        string="Blocked",
        default=False,
        help="Exclude this journal item from customer follow-up actions.",
    )
    def _compute_get_result(self):
        for aml in self:
            aml.result = aml.debit - aml.credit
