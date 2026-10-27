# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# pylint: disable=E0401,C0114,C0115,C0116

from odoo.exceptions import UserError

from odoo import api, fields, models, _


class MpesaPaymentManualReconcile(models.TransientModel):
    _name = "mpesa.payment.manual.reconcile"
    _description = "Mpesa Payment Manual Reconcile"

    @api.model
    def default_get(self, fields_list):
        res = super(MpesaPaymentManualReconcile, self).default_get(fields_list)
        active_ids = self.env.context.get("active_ids", []) or []
        mpesa_transaction_obj = self.env["mpesa.payment.transaction"].browse(
            active_ids[0]
        )

        trans_amount = mpesa_transaction_obj.trans_amount
        student_obj = (
            self.env["xe.student"].search(
                [("roll_number", "=", mpesa_transaction_obj.bill_ref_number)]
            )
            and self.env["xe.student"].search(
                [("roll_number", "=", mpesa_transaction_obj.bill_ref_number)]
            )[0]
        )
        partner_id = (
            student_obj
            and student_obj.partner_id
            and student_obj.partner_id.id
            or False
        )
        # journal_id = self.env.ref('mpesa_transaction_integration.mpesa_journal').id or False
        journal_id = (
            self.env["account.journal"]
            .sudo()
            .search([("company_id", "=", self.env.company.id), ("name", "=", "Mpesa")])
        )
        res.update(
            {
                "trans_amount": trans_amount,
                "student_id": partner_id,
                "journal_id": journal_id,
            }
        )
        return res

    reconcile_method = fields.Selection(
        [("invoice", "Invoice"), ("payment", "Payment Voucher")],
        default="invoice",
    )
    invoice_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        domain=[("state", "=", "posted"), ("move_type", "=", "out_invoice")],
    )
    payment_ids = fields.Many2many(
        "account.payment",
        string="Payments",
        domain=[("state", "=", "draft"), ("payment_type", "=", "inbound")],
    )
    # invoice_id = fields.Many2one('account.invoice', string="", domain=[('state', '=', 'open')])

    trans_amount = fields.Float()
    student_id = fields.Many2one("res.partner")
    journal_id = fields.Many2one("account.journal")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    def make_payment_reconcile(self):
        if self.reconcile_method == "invoice":
            transaction = self.env["mpesa.payment.transaction"].browse(
                self.env.context.get("active_id", False)
            )

            total_inv_amount = 0
            total_reg_amount = sum(self.invoice_ids.mapped('reg_payment'))
            if total_reg_amount and total_reg_amount > transaction.trans_amount or total_reg_amount < transaction.trans_amount:
                raise UserError(_("The total registered amount and transaction amount do not match."))
            # if total_reg_amount and total_reg_amount > transaction.trans_amount:
            #     raise UserError(_("Total register amount you entered is greater than received amount."))

            # if total_reg_amount and total_reg_amount < transaction.trans_amount:
            #     raise UserError(_("Total register amount you entered is less than received amount."))

            for inv in self.invoice_ids:
                reg_amount = inv.reg_payment
                if not reg_amount:
                    raise UserError(_("Register amount should be greater than zero."))

                total_inv_amount = total_inv_amount + reg_amount
                transaction.with_context(
                    manual=True, invoice_id=[inv.id]
                ).validate_invoice_payment_with_regpayment(reg_amount)
                inv.reg_payment = 0

        if self.reconcile_method == "payment":
            self.ensure_one()
            if len(self.payment_ids.ids) == 0:
                raise UserError(_("Please Select one Payment."))
            transaction = self.env["mpesa.payment.transaction"].browse(
                self.env.context.get("active_id", False)
            )

            total_amount = sum(self.payment_ids.mapped('amount'))
            if total_amount and total_amount > transaction.trans_amount or total_amount < transaction.trans_amount:
                raise UserError(_("The total registered amount and transaction amount do not match."))
            # if total_amount and total_amount > transaction.trans_amount:
            #     raise UserError(_("Total amount is greater than received amount."))

            # if total_amount and total_amount < transaction.trans_amount:
            #     raise UserError(_("Total amount is less than received amount."))

            transaction.with_context(
                manual=True, payment_id=self.payment_ids.ids
            ).reconcile_payment_voucher()
        return True

    def view_manual_reconcile(self):
        active_id = self.env.context.get('active_id')
        mpesa_id = self.env['mpesa.payment.transaction'].browse(active_id)
        if mpesa_id.state == 'done':
            raise UserError(_("Transaction already Reconciled!"))
        if mpesa_id.state == "cancel":
            raise UserError(_("Transaction is Cancelled!"))
        action = {
            "name": _("Manual Reconcile"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mpesa.payment.manual.reconcile",
            "target": "new",
        }
        return action

