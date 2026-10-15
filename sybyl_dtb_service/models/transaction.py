# pylint: disable=E0401,C0114,C0115,C0116,R1725
import logging

from odoo.exceptions import UserError

from odoo import models, api, fields, _
# from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class DTBBankTransaction(models.Model):
    _name = "dtb.transaction"
    _description = "DTB Transactions"

    name = fields.Char(string="ReceiptNumber")
    xref = fields.Char("Reference Number")
    bill_ref_no = fields.Char("Bill Reference Number")
    cbs_reference = fields.Char(string="Core Banking Reference")
    cbs_module = fields.Char(string="Core Banking Module")
    account_number = fields.Char()
    branch_code = fields.Char()
    currency = fields.Char()
    dtTransDate = fields.Date(string="Transaction Time")
    value_date = fields.Char()
    dblAmount = fields.Float(
        string="Transaction Amount", digits='Account', required=True
    )
    reversal_indicator = fields.Char()
    debit_credit_indicator = fields.Char("Debit or Credit Indicator")
    exchange_rate = fields.Char()
    financial_year = fields.Char()
    transaction_code = fields.Char()
    transaction_description = fields.Char()
    virtual_pan = fields.Char("Virtual PAN")
    rrn = fields.Char("Retrieval Reference Number")
    customer_name = fields.Char()
    customer_mobile = fields.Char()
    serial_number = fields.Char()
    narration = fields.Char()
    company_id = fields.Many2one(
        "res.company",
        index=True,
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Reconciled"), ("cancel", "Cancelled")],
        default="draft",
    )
    payment_ids = fields.Many2many("account.payment", string="Payments")
    move_id = fields.Many2one("account.move", string="Invoice")
    move_ids = fields.Many2many("account.move", string="Invoices")
    move_name = fields.Char(string="Invoice Name")
    balance = fields.Char()
    transaction_time = fields.Char()

    def state_cancel(self):
        self.ensure_one()
        self.write({"state": "cancel"})

    def state_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    def remove_space_string(self, string):
        if not string:
            return ""
        return string.replace(" ", "")

    @api.model
    def create(self, vals):
        if (
            vals.get("bill_ref_no")
            and vals.get("debit_credit_indicator")
            and vals.get("debit_credit_indicator") == "C"
        ):
            bill_ref = self.remove_space_string(vals.get("bill_ref_no"))
            if not bill_ref.isupper():
                bill_ref = bill_ref.upper()
            if bill_ref.find("-") != -1:
                bill_ref = bill_ref.replace("-", "/")
            invoice = self.env["account.move"].search(
                [
                    ("roll_number", "=", bill_ref),
                    ("state", "not in", ["draft", "cancel"]),
                    ("move_type", "=", "out_invoice"),
                ]
            )
            vals["move_id"] = invoice.id
            vals["move_name"] = invoice.name
        vals["name"] = self.env["ir.sequence"].next_by_code("dtb.transaction") or _(
            "New"
        )
        result = super(DTBBankTransaction, self).create(vals)
        return result

    def validate_move_payment_new(self):
        # draft_entries = self.env['dtb.transaction'].search([('state', '=', 'draft')])
        for line in self:
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = self.env["account.journal"].search(
                [("is_dtb_journal", "=", True)]
            )
            if not account_journal:
                _logger.warning(_("There is no journal for DTB Payment."))
                raise UserError(_("There is no journal for DTB Payment."))
            account_payment_method = self.env["account.payment.method"].search(
                [("code", "=", "manual")]
            )[0]
            method_line_id = self.env["account.payment.method.line"].search(
                [
                    ("journal_id", "=", account_journal.id),
                    ("payment_method_id", "=", account_payment_method.id),
                ]
            )[0]
            move = False
            if line.move_id:
                move = line.move_id
            if context.get("manual"):
                move = False
                line.move_id = False
                if context.get("move_id"):
                    move = self.env["account.move"].search(
                        [("id", "in", context.get("move_id"))]
                    )
                if context.get("payment_id"):
                    payment = self.env["account.payment"].search(
                        [("id", "in", context.get("payment_id"))]
                    )
            if not move:
                if cron:
                    return True
                else:
                    if not context.get("payment_id"):
                        raise UserError(
                            _("Reconcile this transaction manually from action option!")
                        )

            if move and len(move) == 1:
                if move.state not in ["posted", "cancel"]:
                    move.make_dtb_register(line, account_journal, method_line_id)
            if payment:
                payment.action_post()
                line.write({"state": "done", "payment_ids": [(6, 0, payment.ids)]})

    def validate_invoice_payment_with_regpayment(self, reg_amount):
        for r in self:
            r.ensure_one()
            context = self.env.context
            payment = False
            account_journal = self.env["account.journal"].search(
                [("is_dtb_journal", "=", True)]
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
            if context.get("manual"):
                if context.get("invoice_id"):
                    invoices = self.env["account.move"].search(
                        [("id", "in", context.get("invoice_id"))]
                    )
                if context.get("payment_id"):
                    invoice = False
                    payment = self.env["account.payment"].search(
                        [("id", "in", context.get("payment_id"))]
                    )
            if invoices:
                payments_lst = []
                last_inv = False
                for invoice in invoices:
                    if invoice.state not in ["draft", "cancel"]:
                        vals = {
                            "amount": invoice.reg_payment,
                            "partner_type": "customer",
                            "payment_date": self.create_date,
                            "communication": self.narration,
                            "journal_id": account_journal[0].id,
                            # 'hide_payment_method': True,
                            "payment_method_line_id": method_line_id.id,
                        }
                        if self.debit_credit_indicator == "D":
                            vals["partner_type"] = "supplier"
                        register_payments = (
                            self.env["account.payment.register"]
                            .with_context(
                                {
                                    "active_ids": invoice.ids,
                                    "active_model": "account.move",
                                }
                            )
                            .create(vals)
                        )
                        payments = register_payments._create_payments()
                        payments_lst += payments.ids
                        last_inv = invoice.id
                self.write(
                    {
                        "state": "done",
                        "move_id": last_inv,
                        "payment_ids": [(6, 0, payments_lst)],
                        "move_ids": [(6, 0, invoices.ids)],
                    }
                )
            if payment:
                payment.action_post()
                r.write(
                    {
                        "state": "done",
                        "payment_ids": [(6, 0, payment.ids)],
                        "invoice_id": False,
                    }
                )

    def _cron_validate_move_payment_new(self):
        draft_entries = self.env["dtb.transaction"].search([("state", "=", "draft")])
        for line in draft_entries:
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = self.env["account.journal"].search(
                [("is_dtb_journal", "=", True)]
            )
            if not account_journal:
                _logger.warning(_("There is no journal for DTB Payment."))
                raise UserError(_("There is no journal for DTB Payment."))
            account_payment_method = self.env["account.payment.method"].search(
                [("code", "=", "manual")]
            )[0]
            method_line_id = self.env["account.payment.method.line"].search(
                [
                    ("journal_id", "=", account_journal.id),
                    ("payment_method_id", "=", account_payment_method.id),
                ]
            )[0]
            move = False
            if line.move_id:
                move = line.move_id
            if context.get("manual"):
                if context.get("move_id"):
                    move = self.env["account.move"].search(
                        [("id", "in", context.get("move_id"))]
                    )
                if context.get("payment_id"):
                    payment = self.env["account.payment"].search(
                        [("id", "in", context.get("payment_id"))]
                    )
            if not move:
                if cron:
                    return True
                else:
                    if not context.get("payment_id"):
                        raise UserError(
                            _("Reconcile this transaction manually from action option!")
                        )
            if move and len(move) == 1:
                if move.state not in ["draft", "paid", "cancel"]:
                    try:
                        move.make_dtb_register(line, account_journal, method_line_id)
                    except Exception as error:
                        _logger.info(error)
            if payment:
                try:
                    payment.action_post()
                    line.write({"state": "done", "payment_ids": [(6, 0, payment.ids)]})
                except Exception as error:
                    _logger.info(error)
