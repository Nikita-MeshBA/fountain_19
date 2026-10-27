# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

import logging
from datetime import date

from odoo.exceptions import UserError

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class MpesaPaymentTransaction(models.Model):
    _name = "mpesa.payment.transaction"
    _description = "Mpesa Cash Payment Transaction"
    _order = "date"

    name = fields.Char(required=True, index=True)
    ref = fields.Char(string="Paybill/ShortCode", copy=False, index=True)
    datas = fields.Text(string="Json Datas")
    date = fields.Date()
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Reconciled"), ("cancel", "Cancelled")],
        default="draft",
    )
    transaction_type = fields.Char()
    trans_id = fields.Char(string="TransID")
    trans_time = fields.Char(string="TransTime")
    trans_amount = fields.Float()
    business_shortcode = fields.Char()
    bill_ref_number = fields.Char(string="BillRefNumber")
    invoice_number = fields.Char(string="InvoiceNumber")
    org_account_balance = fields.Char()
    third_party_transid = fields.Char(string="ThirdPartyTransID")
    msisdn = fields.Char(string="MSISDN")
    first_name = fields.Char(string="FirstName")
    middle_name = fields.Char(string="MiddleName")
    last_name = fields.Char(string="LastName")
    payment_ids = fields.Many2many("account.payment", string="Payments")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    invoice_name = fields.Char(
        compute="_compute_invoice_name",
        store=True,
        default=lambda self: self._compute_invoice_name(),
        readonly=True,
    )
    company_id = fields.Many2one("res.company")

    @api.model
    def _cron_generate_invoice_payment_entries(self):
        pass
        # for tran in self.search([("state", "=", "draft")], order="id asc"):
        #     if tran.create_date.date() == date.today():
        #         tran.with_context(cron=True).validate_invoice_payment_new()

    @api.model
    def _cron_match_invoice_payment_entries(self):
        payment_method = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mpesa_transaction_integration.transaction_by")
        )
        transactions = self.env["mpesa.payment.transaction"].search(
            [("state", "=", "draft")]
        )
        for tran in transactions:
            invoices = []
            if not tran.invoice_id:
                str_space = self.remove_space_string(tran.bill_ref_number)
                if not str_space.isupper():
                    str_space = str_space.upper()
                if str_space.find("-") != -1:
                    str_space = str_space.replace("-", "/")
                if payment_method == "invoice_no":
                    invoices = self.env["account.move"].search(
                        [("name", "=", str_space)]
                    )
                elif payment_method == "grn":
                    invoices = self.env["account.move"].search(
                        [
                            ("roll_number", "=", str_space),
                            ("state", "not in", ["draft", "cancel"]),
                            ("move_type", "=", "out_invoice"),
                            ("amount_residual", ">", 0),
                        ],
                        limit=1,
                    )
                if len(invoices) == 1:
                    invoice = invoices
                    tran.write({"invoice_id": invoice.id, "invoice_name": invoice.name})
                    tran.with_context(cron=True).validate_invoice_payment_new()
            else:
                if tran.invoice_id and tran.invoice_name:
                    tran.with_context(cron=True).validate_invoice_payment_new()

    ''' '''
    # def validate_invoice_payment_new(self):
    #     self.ensure_one()
    #     reconciliation_val = (
    #         self.env["res.config.settings"]
    #         .sudo()
    #         .get_values()
    #         .get("transaction_by", None)
    #     )
    #     context = self.env.context
    #     cron = context.get("cron", False)
    #     payment = False
    #     # account_journal = self.env['account.journal'].search([('is_mpesa_journal', '=', True)])
    #     account_journal_ids = (
    #         self.env["account.journal"]
    #         .sudo()
    #         .search([("is_mpesa_journal", "=", True), ("name", "=", "Mpesa")])
    #     )
    #     if not account_journal_ids:
    #         _logger.warning(_("There is no journal for mpesa payment."))
    #         raise UserError(_("There is no journal for mpesa payment."))
    #     account_payment_method = self.env["account.payment.method"].search(
    #         [("code", "=", "manual")]
    #     )[0]
    #     for account_journal in account_journal_ids:
    #         if (
    #             self.company_id
    #             and account_journal.company_id
    #             and account_journal.company_id.id == self.company_id.id
    #         ):
    #             method_line_id = self.env["account.payment.method.line"].search(
    #                 [
    #                     ("journal_id", "=", account_journal.id),
    #                     ("payment_method_id", "=", account_payment_method.id),
    #                 ]
    #             )[0]
    #             invoice = self.invoice_id
    #             if not invoice and reconciliation_val and reconciliation_val == "grn":
    #                 invoice = self.env["account.move"].search(
    #                     [
    #                         ("company_id", "=", self.company_id.id),
    #                         ("roll_number", "=", self.bill_ref_number),
    #                         ("state", "not in", ["draft", "cancel"]),
    #                         (
    #                             "payment_state",
    #                             "not in",
    #                             ["paid", "reversed", "in_payment"],
    #                         ),
    #                     ],
    #                     order="invoice_date asc",
    #                 )
    #             if (
    #                 not invoice
    #                 and reconciliation_val
    #                 and reconciliation_val == "invoice_no"
    #             ):
    #                 invoice = self.env["account.move"].search(
    #                     [
    #                         ("company_id", "=", self.company_id.id),
    #                         ("name", "=", self.invoice_number),
    #                         ("state", "not in", ["draft", "cancel"]),
    #                         (
    #                             "payment_state",
    #                             "not in",
    #                             ["paid", "reversed", "in_payment"],
    #                         ),
    #                     ],
    #                     order="invoice_date asc",
    #                 )
    #             if context.get("manual"):
    #                 if context.get("invoice_id"):
    #                     invoice = self.env["account.move"].search(
    #                         [("id", "in", context.get("invoice_id"))]
    #                     )
    #                 if context.get("payment_id"):
    #                     invoice = False
    #                     payment = self.env["account.payment"].search(
    #                         [("id", "in", context.get("payment_id"))]
    #                     )
    #             if not invoice:
    #                 if cron:
    #                     return True
    #                 else:
    #                     if not context.get("payment_id"):
    #                         raise UserError(
    #                             _(
    #                                 "Reconcile this transaction manually from action option!!"
    #                             )
    #                         )
    #             try:
    #                 if invoice and len(invoice) > 1:
    #                     mpesa_trans_amount = self.trans_amount
    #                     invoice_count = len(invoice)
    #                     for inv in invoice:
    #                         if not mpesa_trans_amount:
    #                             break
    #                         if inv.amount_residual > 0:
    #                             invoice_count -= 1
    #                             payment_difference = None
    #                             vals = {}

    #                             if inv.amount_residual <= mpesa_trans_amount:
    #                                 deb_amount = inv.amount_residual
    #                                 vals.update({"amount": inv.amount_residual})
    #                                 if not invoice_count:
    #                                     vals.update({"amount": mpesa_trans_amount})
    #                                     payment_difference = float(
    #                                         mpesa_trans_amount - deb_amount
    #                                     )
    #                                 mpesa_trans_amount -= deb_amount
    #                             else:
    #                                 deb_amount = inv.amount_residual
    #                                 vals.update({"amount": mpesa_trans_amount})
    #                                 mpesa_trans_amount -= mpesa_trans_amount
    #                                 if not mpesa_trans_amount and not invoice_count:
    #                                     payment_difference = float(
    #                                         mpesa_trans_amount - deb_amount
    #                                     )
    #                             vals.update(
    #                                 {
    #                                     "partner_type": "customer",
    #                                     "payment_date": self.date,
    #                                     "communication": self.trans_id,
    #                                     "journal_id": account_journal[0].id,
    #                                     "payment_method_line_id": method_line_id.id,
    #                                 }
    #                             )
    #                             if payment_difference:
    #                                 vals["payment_difference"] = payment_difference
    #                                 vals["payment_difference_handling"] = "open"
    #                             register_payments = (
    #                                 self.env["account.payment.register"]
    #                                 .with_context(
    #                                     active_ids=inv.ids,
    #                                     active_model="account.move",
    #                                 )
    #                                 .create(vals)
    #                             )
    #                             payments = register_payments._create_payments()
    #                             self.write(
    #                                 {"state": "done", "payment_ids": [(4, payments.id)]}
    #                             )
    #                 else:
    #                     if invoice.amount_residual > 0:
    #                         vals = {
    #                             "amount": self.trans_amount,
    #                             "partner_type": "customer",
    #                             "payment_date": self.date,
    #                             "communication": self.trans_id,
    #                             "journal_id": account_journal[0].id,
    #                             "payment_method_line_id": method_line_id.id,
    #                         }
    #                         payment_difference = float(
    #                             self.trans_amount - invoice.amount_residual
    #                         )
    #                         if payment_difference:
    #                             vals["payment_difference"] = payment_difference
    #                             vals["payment_difference_handling"] = "open"
    #                         register_payments = (
    #                             self.env["account.payment.register"]
    #                             .with_context(
    #                                 active_ids=invoice.ids,
    #                                 active_model="account.move",
    #                             )
    #                             .create(vals)
    #                         )
    #                         payments = register_payments._create_payments()
    #                         self.write(
    #                             {"state": "done", "payment_ids": [(4, payments.id)]}
    #                         )
    #                     else:
    #                         if not cron:
    #                             raise UserError(
    #                                 _(
    #                                     "Reconcile this transaction manually from action option!!"
    #                                 )
    #                             )
    #                 if payment:
    #                     payment.action_post()
    #                     self.write(
    #                         {
    #                             "state": "done",
    #                             "payment_ids": [(6, 0, payment.ids)],
    #                             "invoice_id": False,
    #                         }
    #                     )
    #             except Exception as error:
    #                 _logger.warning(
    #                     f"Mpesa transaction not reconcile for {self.bill_ref_number}"
    #                 )

    def validate_invoice_payment_with_regpayment(self, reg_amount):
        for record in self:
            record.ensure_one()
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = self.env["account.journal"].search(
                [("is_mpesa_journal", "=", True)]
            )
            account_journal = (
                self.env["account.journal"]
                .sudo()
                .search(
                    [("company_id", "=", self.env.company.id), ("name", "=", "Mpesa")],
                    limit=1,
                )
            )
            if not account_journal:
                _logger.warning(_("There is no journal for mpesa payment."))
                raise UserError(_("There is no journal for mpesa payment."))
            account_payment_method = self.env["account.payment.method"].search(
                [("code", "=", "manual")]
            )[0]
            method_line_id = self.env["account.payment.method.line"].search(
                [
                    ("journal_id", "=", account_journal.id),
                    ("payment_method_id", "=", account_payment_method.id),
                ]
            )[0]
            invoice = record.invoice_id
            if not invoice:
                invoice = self.env["account.move"].search(
                    [("name", "=", record.invoice_number)]
                )
            if context.get("manual"):
                if context.get("invoice_id"):
                    invoice = self.env["account.move"].search(
                        [("id", "in", context.get("invoice_id"))]
                    )
                if context.get("payment_id"):
                    invoice = False
                    payment = self.env["account.payment"].search(
                        [("id", "in", context.get("payment_id"))]
                    )
            if not invoice:
                if cron:
                    return True
                else:
                    if not context.get("payment_id"):
                        raise UserError(
                            _("Reconcile this transaction manually from action option!")
                        )
            if invoice and len(invoice) == 1:
                if invoice.state not in ["draft", "paid", "cancel"]:
                    vals = {
                        "amount": reg_amount,
                        "partner_type": "customer",
                        "payment_date": self.date,
                        "communication": self.trans_id,
                        "journal_id": account_journal[0].id,
                        # 'hide_payment_method': True,
                        "payment_method_line_id": method_line_id.id,
                    }
                    register_payments = (
                        self.env["account.payment.register"]
                        .with_context(
                            active_ids=invoice.ids,
                            active_model="account.move",
                        )
                        .create(vals)
                    )
                    record.update({"invoice_id": invoice.id})
                    payments = register_payments._create_payments()
                    record.update(
                        {
                            "state": "done",
                            "payment_ids": [(4, payments.id)],
                        }
                    )
            if payment:
                payment.action_post()
                record.update(
                    {
                        "state": "done",
                        "payment_ids": [(6, 0, payment.ids)],
                        "invoice_id": False,
                    }
                )

    def validate_invoice_payment(self):
        payment_created = False
        move_id = self.env["account.move"].search([("name", "=", self.bill_ref_number)], limit=1)
        student_id = self.env["xe.student"].with_context(active_test=False).search([("roll_number", "=", self.bill_ref_number)], limit=1)
        if not move_id and not student_id:
            raise UserError(_("Account not found !!. Please process this transaction by clicking the Manual Reconcile button."))
            # raise UserError(_("Reconcile this transaction manually from action option!"))

        account_journal = (
            self.env["account.journal"]
            .sudo()
            .search(
                [("company_id", "=", self.env.company.id), ("is_mpesa_journal", "=", True)],
                limit=1,
            )
        )
        if not account_journal:
            raise UserError(_("There is no journal for mpesa payment."))
        account_payment_method = self.env["account.payment.method"].search(
            [("code", "=", "manual")]
        )[0]
        method_line_id = self.env["account.payment.method.line"].search(
            [
                ("journal_id", "=", account_journal.id),
                ("payment_method_id", "=", account_payment_method.id),
            ]
        )[0]

        if move_id:
            if move_id.payment_state == "paid":
                raise UserError(_("You can't register a payment because there is nothing left to pay on the selected journal items."))

            if move_id.state == "posted" and move_id.payment_state in ["not_paid", "partial"]:
                vals = {
                    "amount": self.trans_amount,
                    "partner_type": "customer",
                    "payment_date": self.date,
                    "communication": self.trans_id,
                    "journal_id": account_journal[0].id,
                    "payment_method_line_id": method_line_id.id,
                }
                register_payments = (
                    self.env["account.payment.register"]
                    .with_context(
                        active_ids=move_id.ids,
                        active_model="account.move",
                    )
                    .create(vals)
                )
                payments = register_payments._create_payments()
                if not payments.ref:
                    payments.ref = self.trans_id
                self.write(
                    {
                        "state": "done",
                        "payment_ids": [(4, payments.id)],
                        "invoice_id": move_id.id,
                    }
                )
                payment_created = True

        if student_id and not payment_created:
            vals = {
                "is_internal_transfer": False,
                "payment_type": "inbound",
                "partner_id": student_id.partner_id.id if student_id.partner_id else False,
                "amount": self.trans_amount,
                "company_id": student_id.partner_id.company_id.id,
                "journal_id": account_journal[0].id if account_journal[0] else False,
                "state": "draft",
                "ref": self.trans_id,
                "payment_method_line_id": account_journal[0].inbound_payment_method_line_ids[
                    0
                ].id
                if account_journal[0].inbound_payment_method_line_ids
                else False,
            }
            try:
                payment_id = self.env["account.payment"].sudo().create(vals)
                if payment_id:
                    self.write(
                        {
                            "state": "done",
                            "payment_ids": [(4, payment_id.id)],
                        }
                    )
                    payment_id.action_post()
            except Exception as e:
                _logger.warning(e)

    def button_manual_reconcile_payment(self):
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

    def reconcile_payment_voucher(self):
        for record in self:
            record.ensure_one()
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = self.env["account.journal"].search(
                [("is_mpesa_journal", "=", True)]
            )
            account_journal = (
                self.env["account.journal"]
                .sudo()
                .search(
                    [("company_id", "=", self.env.company.id), ("name", "=", "Mpesa")],
                    limit=1,
                )
            )
            if not account_journal:
                _logger.warning(_("There is no journal for mpesa payment."))
                raise UserError(_("There is no journal for mpesa payment."))
            account_payment_method = self.env["account.payment.method"].search(
                [("code", "=", "manual")]
            )[0]
            method_line_id = self.env["account.payment.method.line"].search(
                [
                    ("journal_id", "=", account_journal.id),
                    ("payment_method_id", "=", account_payment_method.id),
                ]
            )[0]
            invoice = record.invoice_id
            if not invoice:
                invoice = self.env["account.move"].search(
                    [("name", "=", record.invoice_number)]
                )
            if context.get("manual"):
                if context.get("invoice_id"):
                    invoice = self.env["account.move"].search(
                        [("id", "in", context.get("invoice_id"))]
                    )
                if context.get("payment_id"):
                    invoice = False
                    payment = self.env["account.payment"].search(
                        [("id", "in", context.get("payment_id"))]
                    )
            if not invoice:
                if cron:
                    return True
                else:
                    if not context.get("payment_id"):
                        raise UserError(
                            _("Reconcile this transaction manually from action option!")
                        )
            if invoice and len(invoice) == 1:
                if invoice.state not in ["draft", "paid", "cancel"]:
                    vals = {
                        "amount": record.trans_amount,
                        "partner_type": "customer",
                        "payment_date": record.date,
                        "communication": record.trans_id,
                        "journal_id": account_journal[0].id,
                        # 'hide_payment_method': True,
                        "payment_method_line_id": method_line_id.id,
                    }
                    register_payments = (
                        self.env["account.payment.register"]
                        .with_context(
                            active_ids=invoice.ids,
                            active_model="account.move",
                        )
                        .create(vals)
                    )
                    payments = register_payments._create_payments()
                    if not payments.ref:
                        payments.ref = record.trans_id
                    record.write(
                        {"state": "done", "payment_ids": [(4, payments.id)]}
                    )
            if payment:
                for pym in payment:
                    pym.ref = record.trans_id
                    pym.action_post()
                record.write(
                    {
                        "state": "done",
                        "payment_ids": [(6, 0, payment.ids)],
                        "invoice_id": False,
                    }
                )

    def remove_space_string(self, string):
        if not string:
            return ""
        return string.replace(" ", "")

    def state_cancel(self):
        self.ensure_one()
        self.write({"state": "cancel"})

    def state_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    @api.depends("bill_ref_number")
    def _compute_invoice_name(self):
        payment_method = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mpesa_transaction_integration.transaction_by")
        )
        for tran in self:
            str_space = self.remove_space_string(tran.bill_ref_number)
            if not str_space.isupper():
                str_space = str_space.upper()
            if str_space.find("-") != -1:
                str_space = str_space.replace("-", "/")
            tran.invoice_name = str_space
            invoice = self.env["account.move"].search(
                [("name", "=", tran.invoice_name)]
            )
            tran.update({"invoice_id": invoice.id})
            if payment_method == "invoice_no":
                tran.invoice_name = str_space
                invoice = self.env["account.move"].search(
                    [("name", "=", tran.invoice_name)]
                )
            elif payment_method == "grn":
                student = self.env["xe.student"].search(
                    [("roll_number", "=", str_space)]
                )
                if student:
                    invoices = self.env["account.move"].search(
                        [
                            ("partner_id", "=", student.partner_id.id),
                            ("state", "not in", ["draft", "cancel"]),
                            ("move_type", "=", "out_invoice"),
                            ("amount_residual", ">", 0),
                        ],
                        limit=1,
                    )
                    if len(invoices) == 1:
                        invoice = invoices
                        tran.invoice_name = invoice.name
            else:
                tran.invoice_name = False
            if invoice:
                tran.update({"invoice_id": invoice.id})

    def view_manual_reconcile(self):
        action = {
            "name": _("Manual Reconcile"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mpesa.payment.manual.reconcile",
            "target": "new",
        }
        return action
