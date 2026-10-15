# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# pylint: disable=E0401,C0114,C0115,C0116
from odoo.exceptions import UserError

from odoo import api, fields, models, _


class DTBPaymentManualReconcile(models.TransientModel):
    _name = "dtb.payment.manual.reconcile"
    _description = "DTB Payment Manual Reconcile"

    @api.onchange("transaction_id")
    def _get_payment_type(self):
        for record in self:
            if record.transaction_id:
                if record.transaction_id.debit_credit_indicator == "D":
                    record.payment_type = "payable"
                else:
                    record.payment_type = "receivable"

    transaction_id = fields.Many2one(
        "dtb.transaction", default=lambda self: self.env.context.get("active_id", False)
    )
    payment_type = fields.Selection(
        [("receivable", "Receivable"), ("payable", "Payable")]
    )
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
    bill_ids = fields.Many2many(
        "account.move", "dtb_bill_rel", "wizard_id", "bill_id", string="Vendor Bills"
    )
    payment_voucher_ids = fields.Many2many(
        "account.payment",
        "dtb_payment_rel",
        "wizard_id",
        "payment_id",
        string="Payment Vouchers",
        domain=[("state", "=", "draft"), ("payment_type", "=", "outbound")],
    )
    # invoice_id = fields.Many2one('account.invoice', string="", domain=[('state', '=', 'open')])

    trans_amount = fields.Float()
    student_id = fields.Many2one("res.partner")
    journal_id = fields.Many2one("account.journal")

    def make_payment_reconcile(self):
        transaction = self.env["dtb.transaction"].browse(
            self.env.context.get("active_id", False)
        )
        if transaction and transaction.state == "done":
            raise UserError(_("Transaction already Reconciled!"))
        if transaction and transaction.state == "cancel":
            raise UserError(_("Transaction is Cancelled!"))

        if self.reconcile_method == "invoice":
            self.ensure_one()
            if (
                transaction
                and transaction.debit_credit_indicator != "C"
                and self.payment_type == "receivable"
            ):
                raise UserError(
                    _("The wrong payment type has been selected for this transaction")
                )
            if (
                transaction
                and transaction.debit_credit_indicator != "D"
                and self.payment_type == "payable"
            ):
                raise UserError(
                    _("The wrong payment type has been selected for this transaction")
                )
            if self.payment_type == "receivable":
                invoice_ids = self.invoice_ids
            else:
                invoice_ids = self.bill_ids
            if len(invoice_ids.ids) == 0:
                raise UserError(_("Please Select at least one invoice."))
            total_amount = 0
            for inv in invoice_ids:
                reg_amount = inv.reg_payment
                if not reg_amount:
                    raise UserError(_("Register amount should be greater than zero"))
                total_amount = total_amount + reg_amount
            if total_amount > transaction.dblAmount:
                raise UserError(
                    _("Total amount you entered is greater than received amount!")
                )
            transaction.with_context(
                {"manual": True, "invoice_id": invoice_ids.ids}
            ).validate_invoice_payment_with_regpayment(reg_amount)
            # transaction.with_context(
            #     {'manual': True, 'move_id': self.invoice_ids.ids}).validate_move_payment_new()
        if self.reconcile_method == "payment":
            self.ensure_one()
            if self.payment_type == "receivable":
                payment_ids = self.payment_ids
            else:
                payment_ids = self.payment_voucher_ids
            if len(payment_ids.ids) == 0:
                raise UserError(_("Please Select one Payment."))
            transaction.with_context(
                {"manual": True, "payment_id": payment_ids.ids}
            ).validate_move_payment_new()
        return True
