# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import UserError

from odoo import models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def unlink(self):
        for move in self:
            fees_line = self.env["xe.student.fees.details"].search(
                [("invoice_id", "=", move.id)]
            )
            if fees_line:
                fees_line.state = "draft"

            if move.posted_before and not self._context.get("force_delete"):
                raise UserError(
                    _("You cannot delete an entry which has been posted once.")
                )
        self.line_ids.unlink()
        return super(AccountMove, self).unlink()
