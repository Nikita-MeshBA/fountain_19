# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# pylint: disable=E0401
from odoo.exceptions import UserError

from odoo import fields, models, _


class KCBPaymentManualReconcile(models.TransientModel):
    _name = "kcb.payment.manual.reconcile"
    _description = "KCB Payment Manual Reconcile"

    reconcile_method = fields.Selection(
        [("invoice", "Invoice"), ("payment", "Payment Voucher")],
        default="invoice",
    )
    invoice_ids = fields.Many2many("account.move", string="Invoices")
    payment_ids = fields.Many2many(
        "account.payment",
        string="Payments",
        domain=[("state", "=", "draft"), ("payment_type", "=", "inbound")],
    )
    # invoice_id = fields.Many2one('account.invoice', string="", domain=[('state', '=', 'open')])
    trans_amount = fields.Float()
    student_id = fields.Many2one("res.partner")
    journal_id = fields.Many2one("account.journal")

    def make_payment_reconcile(self):
        if self.reconcile_method == "invoice":
            self.ensure_one()
            if len(self.invoice_ids.ids) == 0 or len(self.invoice_ids.ids) > 1:
                raise UserError(_("Please Select at least one invoice."))
            transaction = self.env["kcb.transaction"].browse(
                self.env.context.get("active_id", False)
            )
            if transaction and transaction.state == "done":
                raise UserError(_("Transaction already Reconciled!"))

            if transaction and transaction.state == "cancel":
                raise UserError(_("Transaction is Cancelled!"))

            transaction.with_context(
                {"manual": True, "move_id": self.invoice_ids.ids}
            ).validate_move_payment_new()
        if self.reconcile_method == "payment":
            self.ensure_one()
            if len(self.payment_ids.ids) == 0:
                raise UserError(_("Please Select one Payment."))
            transaction = self.env["kcb.transaction"].browse(
                self.env.context.get("active_id", False)
            )
            if transaction and transaction.state == "done":
                raise UserError(_("Transaction already Reconciled!"))

            if transaction and transaction.state == "cancel":
                raise UserError(_("Transaction is Cancelled!"))

            transaction.with_context(
                {"manual": True, "payment_id": self.payment_ids.ids}
            ).validate_move_payment_new()
        return True
