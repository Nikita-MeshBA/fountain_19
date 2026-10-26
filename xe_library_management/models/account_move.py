# -*- coding: utf-8 -*-

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_paid(self):
        paid_invoice = super(AccountMove, self).action_invoice_paid()
        if paid_invoice and self:
            movement = self.env["xe.media.movement"].search([("move_id", "=", self.id)])
            if movement:
                movement.state = "return_done"
        return paid_invoice
