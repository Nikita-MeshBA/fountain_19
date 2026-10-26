# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import logging
_logger = logging.getLogger(__name__)

class CoopBankTransaction(models.Model):
    _name = "coop.bank.transaction"
    _description = "Cooperative Bank Transaction"
    _rec_name = "transaction_reference_code"

    name = fields.Char("serviceName")
    odoo_id = fields.Char("Odoo ID", compute="_compute_odoo_id")
    message_id = fields.Char("messageID")
    connection_id = fields.Char("connectionID")
    transaction_reference_code = fields.Char(string="TransactionReferenceCode")
    transaction_date = fields.Char(string="TransactionDate")
    transaction_datetime = fields.Datetime(string="TransactionDate")
    total_amount = fields.Float(string="TotalAmount")
    currency = fields.Char(string="Currency")
    document_reference_number = fields.Char(string="DocumentReferenceNumber")
    bank_code = fields.Char(string="BankCode")
    branch_code = fields.Char(string="BranchCode")
    payment_date = fields.Char(string="PaymentDate")
    payment_reference_code = fields.Char(string="PaymentReferenceCode")
    payment_code = fields.Char(string="PaymentCode")
    payment_mode = fields.Char(string="PaymentMode")
    payment_amount = fields.Char(string="PaymentAmount")
    additional_info = fields.Char(string="AdditionalInfo")
    account_number = fields.Char(string="AccountNumber")
    account_name = fields.Char(string="AccountName")
    institution_code = fields.Char(string="InstitutionCode")
    institution_name = fields.Char(string="InstitutionName")
    student_id = fields.Many2one("xe.student")
    invoice_id = fields.Many2one("account.move")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.user.company_id
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    invoice_amount = fields.Monetary()
    log_ids = fields.One2many("coop.bank.log", "coop_bank_transaction_id")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Reconciled'), ('cancel', 'Cancelled')], string="State",
                             default="draft")
    payment_ids = fields.Many2many('account.payment', string="Payments")


    def _compute_odoo_id(self):
        for record in self:
            record.odoo_id = "{:05d}".format(record.id)

    def cron_cooperative_bank_payment_creation(self):
        account_journal = self.env['account.journal'].sudo().search(
            [('company_id', '=', self.env.company.id), ('code', '=', 'COOP')],limit=1)
        if not account_journal:
            _logger.warning(_('There is no journal for Cooperative Bank Journal.'))
            raise UserError(_('There is no journal for Cooperative Bank Journal.'))
        for r in self.search([('state','=','draft')]):
            r.ensure_one()
            payment = False
            account_payment_method = self.env['account.payment.method'].search([('code', '=', 'manual')])[0]
            method_line_id = self.env['account.payment.method.line'].search([('journal_id', '=', account_journal.id),
                                                                             ('payment_method_id', '=',
                                                                              account_payment_method.id)])[0]
            # partner = self.env['res.partner'].search([('')])
            partner_id = (self.env["res.partner"].sudo().search([("roll_number","=",r.document_reference_number,)],limit=1,))
            if partner_id:
                vals = {
                    'name': '/',
                    'date': r.transaction_datetime,
                    'invoice_date': r.transaction_datetime,  # expense payment behave as bills
                    'ref': r.payment_reference_code,
                    'move_type': 'entry',
                    'journal_id': account_journal.id,
                }
                payment_vals = {}
                payment_vals.update(vals)
                payment_vals.update({
                    'journal_id': account_journal.id,
                    'amount': r.total_amount,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_line_id': method_line_id.id,
                    'partner_id': partner_id.id,
                })
                payments = self.env['account.payment'].create(payment_vals)
                if payments:
                    payments.action_post()
                    r.write({'state': 'done', 'payment_ids': [(6,0, payments.ids)]})
    
    def state_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})

    def state_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})


    def view_manual_reconcile(self):
        active_id = self.env.context.get('active_id')
        mpesa_id = self.env['coop.bank.transaction'].browse(active_id)
        if mpesa_id.state == 'done':
            raise UserError(_("Transaction already Reconciled!"))
        if mpesa_id.state == "cancel":
            raise UserError(_("Transaction is Cancelled!"))
        action = {
            "name": _("Manual Reconcile"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "coop.payment.manual.reconcile",
            "target": "new",
        }
        return action

    def reconcile_payment_voucher(self):
        for record in self:
            record.ensure_one()
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = (
                self.env["account.journal"]
                .sudo()
                .search(
                    [("company_id", "=", self.env.company.id), ("code", "=", "COOP")],
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
                        "amount": record.total_amount,
                        "partner_type": "customer",
                        "payment_date": record.transaction_date,
                        "communication": record.payment_reference_code,
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
                        payments.ref = record.message_id
                    record.write(
                        {"state": "done", "payment_ids": [(4, payments.id)]}
                    )
            if payment:
                for pym in payment:
                    pym.ref = record.message_id
                    pym.action_post()
                record.write(
                    {
                        "state": "done",
                        "payment_ids": [(6, 0, payment.ids)],
                        "invoice_id": False,
                    }
                )

    def validate_invoice_payment_with_regpayment(self, reg_amount):
        for record in self:
            record.ensure_one()
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = (
                self.env["account.journal"]
                .sudo()
                .search(
                    [("company_id", "=", self.env.company.id), ("code", "=", "COOP")],
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
            print ('___ invoice : ', invoice);
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
            print ('___ invoice : ', invoice);
            if invoice and len(invoice) == 1:
                if invoice.state not in ["draft", "paid", "cancel"]:
                    vals = {
                        "amount": reg_amount,
                        "partner_type": "customer",
                        "payment_date": self.transaction_date,
                        "communication": self.payment_reference_code,
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

