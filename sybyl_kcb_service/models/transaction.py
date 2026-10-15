# pylint: disable=E0401,C0116

import logging

from odoo.exceptions import UserError

from odoo import models, api, fields, _
# from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class KCBBankTransaction(models.Model):
    _name = "kcb.transaction"
    _description = "KCB Transactions"

    name = fields.Char(string="ReceiptNumber")
    dblAmount = fields.Float(
        string="Amount", digits='Account', required=True
    )
    strTransNo = fields.Char(string="Transaction Number", required=True, index=True)
    dtTransDate = fields.Date(string="Transaction Date", required=True)
    request_id = fields.Char()
    bill_ref_no = fields.Char("Bill Reference Number")
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
    move_name = fields.Char(string="Invoice Name")
    businessKeyType = fields.Char("Business Key Type")
    notifybusinessKey = fields.Char("Notification Business Key")
    notifybusinessKeyType = fields.Char("Notification Business Key Type")
    debitMSISDN = fields.Char("debitMSISDN")
    firstName = fields.Char("firstName")
    middleName = fields.Char("middleName")
    lastName = fields.Char("lastName")
    mobile = fields.Char()
    creditAccountIdentifier = fields.Char("CreditAccountIdentifier")
    currency = fields.Char()
    narration = fields.Char()
    transactionType = fields.Char("transactionType")
    balance = fields.Char()

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
        if vals.get("bill_ref_no"):
            bill_ref = self.remove_space_string(vals.get("bill_ref_no"))
            if not bill_ref.isupper():
                bill_ref = bill_ref.upper()
            if bill_ref.find("-") != -1:
                bill_ref = bill_ref.replace("-", "/")
            invoice = self.env["account.move"].search([("bill_ref_no", "=", bill_ref)])
            vals["move_id"] = invoice.id
            vals["move_name"] = invoice.name
            # vals["bill_ref_no"] = bill_ref
            # vals["bill_ref_no"] = invoice.partner_id.roll_number
        vals["name"] = self.env["ir.sequence"].next_by_code("kcb.transaction") or _(
            "New"
        )
        result = super(KCBBankTransaction, self).create(vals)
        return result

    def validate_move_payment_new_cron(self):
        draft_entries = self.env["kcb.transaction"].search([("state", "=", "draft")])
        for line in draft_entries:
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = self.env["account.journal"].search(
                [("is_kcb_journal", "=", True)]
            )
            if not account_journal:
                _logger.warning(_("There is no journal for KCB Payment."))
                raise UserError(_("There is no journal for KCB Payment."))
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
                    move.make_kcb_register(line, account_journal, method_line_id)
            if payment:
                payment.action_post()
                payment.write({"ref": line.name})
                line.write({"state": "done", "payment_ids": [(6, 0, payment.ids)]})

    def validate_move_payment_new(self):
        draft_entries = self
        for line in draft_entries:
            context = self.env.context
            cron = context.get("cron", False)
            payment = False
            account_journal = self.env["account.journal"].search(
                [("is_kcb_journal", "=", True)]
            )
            if not account_journal:
                _logger.warning(_("There is no journal for KCB Payment."))
                raise UserError(_("There is no journal for KCB Payment."))
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
                    move.make_kcb_register(line, account_journal, method_line_id)
            if payment:
                payment.action_post()
                payment.write({"ref": line.name})
                line.write(
                    {
                        "state": "done",
                        "payment_ids": [(6, 0, payment.ids)],
                        "move_id": False,
                    }
                )
