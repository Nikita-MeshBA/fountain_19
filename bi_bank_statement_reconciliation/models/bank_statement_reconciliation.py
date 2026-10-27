from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, _


class BankStatementReconciliation(models.Model):
    _name = "bank.statement.reconciliation"
    _description = "Bank Statement Reconciliation"

    name = fields.Char(required=True, copy=False)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    reconciled_balance = fields.Float(compute="_compute_reconciled_balance")
    foreigh_reconciled_balance = fields.Float(
        string="Reconciled Balance", compute="_compute_reconciled_balance_foreigh"
    )

    def add_domain(self):
        return [
            (
                "user_type_id",
                "=",
                self.env.ref("accounting_pdf_reports.data_account_type_liquidity").id,
            )
        ]

    account_id = fields.Many2one(
        "account.account",
        domain=add_domain,
    )
    line_ids = fields.Many2many(
        "account.move.line",
        string="Account Move",
        copy=False,
    )
    opening_balance = fields.Float(
        copy=False, compute="_compute_opening_balance", store=True
    )
    book_closing_balance = fields.Float(
        compute="_compute_closing_balance",
        store=True,
        copy=False,
    )
    foreigh_book_closing_balance = fields.Float(
        string="Book Closing Balance",
        compute="_compute_closing_balance_foreigh",
        store=True,
        copy=False,
    )
    foreigh_display_currency = fields.Many2one("res.currency", string="Currency")
    actual_closing_balance = fields.Float(
        string="Bank Statement Closing Balance", copy=False
    )
    foreigh_actual_closing_balance = fields.Float(
        string="Bank Statement Closing Balance", copy=False
    )

    difference = fields.Float(copy=False)
    foreigh_difference = fields.Float(string="Difference", copy=False)
    new_diff_amt = fields.Float("Difference Amount")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("confirm", "Confirm")],
        default="draft",
    )
    remarks = fields.Text()
    currency_id = fields.Many2one("res.currency")
    bal_type = fields.Char(readonly=True)

    @api.onchange("actual_closing_balance", "difference")
    def set_foreigh_actual_closing_balance_foreigh_difference(self):
        rate = self.env["res.currency.rate"].search(
            [("currency_id", "=", self.currency_id.id)], order="id desc", limit=1
        )
        if rate:
            self.foreigh_actual_closing_balance = (
                self.actual_closing_balance / rate.inverse_company_rate
            )
            self.foreigh_difference = self.difference / rate.inverse_company_rate
        self.new_diff_amt = self.book_closing_balance - self.difference

    @api.onchange("foreigh_actual_closing_balance", "difference")
    def set_actual_closing_balance(self):
        rate = self.env["res.currency.rate"].search(
            [("currency_id", "=", self.currency_id.id)], order="id desc", limit=1
        )
        self.actual_closing_balance = (
            self.foreigh_actual_closing_balance * rate.inverse_company_rate
        )
        self.difference = self.foreigh_difference * rate.inverse_company_rate

    @api.depends("line_ids")
    def _compute_reconciled_balance_foreigh(self):
        positvi_val = nagtiv_val = 0
        for res in self:
            res.foreigh_reconciled_balance = 0.0
            for i in res.line_ids:
                if i.is_present_bank_statement and i.display_amount > 0:
                    positvi_val += i.display_amount
                if i.is_present_bank_statement and i.display_amount < 0:
                    nagtiv_val += i.display_amount
            res.foreigh_reconciled_balance = positvi_val - abs(nagtiv_val)

    @api.depends("line_ids")
    def _compute_closing_balance_foreigh(self):
        for record in self:
            if (
                record.account_id
                and record.start_date
                and record.end_date
                and record.currency_id
            ):
                closing_balance_query = f"""
                    SELECT SUM(display_amount) from account_move_line
                    WHERE account_id = {record.account_id.id}
                    AND date <= '{record.end_date}'
                    AND currency_id = {record.currency_id.id}
                    AND parent_state = 'posted'
                """
                self.env.cr.execute(closing_balance_query)
                foreigh_book_closing_balance = self.env.cr.dictfetchone()
                if foreigh_book_closing_balance.get("sum", False):
                    record.foreigh_book_closing_balance = foreigh_book_closing_balance[
                        "sum"
                    ]
                else:
                    record.foreigh_book_closing_balance = 0
        for res in self:
            for i in res.line_ids:
                # if i.display_amount > 0:
                #     res.foreigh_book_closing_balance += i.display_amount
                # if i.display_amount < 0:
                #     res.foreigh_book_closing_balance -= i.display_amount
                res.foreigh_display_currency = (
                    self.env["res.currency"]
                    .sudo()
                    .search([("name", "=", i.display_currency)])
                )

    def action_refresh(self):
        for order in self:
            order._onchange_dates()
            order._onchange_difference()
            # order.set_foreigh_actual_closing_balance_foreigh_difference()

    @api.onchange("account_id")
    def _onchange_account_id(self):
        for each in self:
            each.currency_id = each.account_id.currency_id
            each._onchange_dates()

    @api.onchange("closing_balance", "closing")
    def _onchange_difference(self):
        for order in self:
            order.difference = (
                order.book_closing_balance - order.actual_closing_balance
            ) - order.new_diff_amt

    def action_confirm(self):
        for order in self:
            # if order.line_ids.filtered(lambda x: not x.is_present_bank_statement):
            #     raise ValidationError(_("All entries must be present in the bank statement"))
            if order.book_closing_balance and not order.actual_closing_balance:
                raise ValidationError(
                    _("Please enter the bank statement closing balance.")
                )
            if order.difference != 0:
                raise ValidationError(
                    _(
                        "Difference is not zero. Please correct it or try clicking the Refresh Button."
                    )
                )
            for i in order.line_ids:
                if i.is_present_bank_statement and i.transaction_date == False:
                    raise ValidationError(_("Please enter the transaction date"))
            order.state = "confirm"

    @api.onchange("account_id", "start_date", "end_date")
    def _onchange_dates(self):
        for record in self:
            if (
                record.account_id
                and record.start_date
                and record.end_date
                and record.currency_id
            ):
                old_line_ids = (
                    self.env["account.move.line"]
                    .search(
                        [
                            ("account_id", "=", record.account_id.id),
                            ("date", "<", record.start_date),
                            ("currency_id", "=", record.currency_id.id),
                            ("parent_state", "=", "posted"),
                            ("is_present_bank_statement", "=", False),
                        ]
                    )
                    .ids
                )
                new_line_ids = (
                    self.env["account.move.line"]
                    .search(
                        [
                            ("account_id", "=", record.account_id.id),
                            ("date", ">=", record.start_date),
                            ("date", "<=", record.end_date),
                            ("currency_id", "=", record.currency_id.id),
                            ("parent_state", "=", "posted"),
                        ]
                    )
                    .ids
                )
                record.line_ids = [(6, 0, old_line_ids + new_line_ids)]
                opening_balance_query = f"""
                    SELECT SUM(balance) from account_move_line
                    WHERE account_id = {record.account_id.id}
                    AND date < '{record.start_date}'
                    AND currency_id = {record.currency_id.id}
                    AND parent_state = 'posted'
                """
                self.env.cr.execute(opening_balance_query)
                opening_balance = self.env.cr.dictfetchone()
                if opening_balance.get("sum", False):
                    record.opening_balance = opening_balance["sum"]
            else:
                record.line_ids = False

            if record.line_ids:
                for i in record.line_ids:
                    i.display_amount = i.amount_currency
                    i.display_currency = i.currency_id.name

                    # i.display_amount = self.env['account.move'].search([('name', '=',i.move_name)]).line_ids.account_currency
                    # i.display_currency = self.env['account.move'].search([('name', '=',i.move_name)]).currency_id

    @api.depends("line_ids")
    def _compute_closing_balance(self):
        for record in self:
            if (
                record.account_id
                and record.start_date
                and record.end_date
                and record.currency_id
            ):
                closing_balance_query = f"""
                    SELECT SUM(balance) from account_move_line
                    WHERE account_id = {record.account_id.id}
                    AND date <= '{record.end_date}'
                    AND currency_id = {record.currency_id.id}
                    AND parent_state = 'posted'
                """
                self.env.cr.execute(closing_balance_query)
                book_closing_balance = self.env.cr.dictfetchone()
                if book_closing_balance.get("sum", False):
                    record.book_closing_balance = book_closing_balance["sum"]
                else:
                    record.book_closing_balance = 0
                if record.book_closing_balance > 0:
                    record.bal_type = "Debit"
                elif record.book_closing_balance < 0:
                    record.bal_type = "Credit"

    @api.depends("account_id", "start_date", "end_date")
    def _compute_opening_balance(self):
        for record in self:
            if (
                record.account_id
                and record.start_date
                and record.end_date
                and record.currency_id
            ):
                old_line_ids = (
                    self.env["account.move.line"]
                    .search(
                        [
                            ("account_id", "=", record.account_id.id),
                            ("date", "<", record.start_date),
                            ("currency_id", "=", record.currency_id.id),
                            ("parent_state", "=", "posted"),
                            ("is_present_bank_statement", "=", False),
                        ]
                    )
                    .ids
                )
                new_line_ids = (
                    self.env["account.move.line"]
                    .search(
                        [
                            ("account_id", "=", record.account_id.id),
                            ("date", ">=", record.start_date),
                            ("date", "<=", record.end_date),
                            ("currency_id", "=", record.currency_id.id),
                            ("parent_state", "=", "posted"),
                        ]
                    )
                    .ids
                )
                record.line_ids = [(6, 0, old_line_ids + new_line_ids)]
                opening_balance_query = f"""
                    SELECT SUM(balance) from account_move_line
                    WHERE account_id = {record.account_id.id}
                    AND date < '{record.start_date}'
                    AND currency_id = {record.currency_id.id}
                    AND parent_state = 'posted'
                """
                self.env.cr.execute(opening_balance_query)
                opening_balance = self.env.cr.dictfetchone()

                if opening_balance.get("sum", False):
                    record.opening_balance = opening_balance["sum"]

    @api.ondelete(at_uninstall=False)
    def _unlink_if_cancelled(self):
        for order in self:
            if not order.state == "draft":
                raise UserError(_("You cannot delete it in confirmed state."))

    @api.depends("line_ids")
    def _compute_reconciled_balance(self):
        for record in self:
            record.reconciled_balance = sum(
                record.line_ids.filtered(lambda x: x.is_present_bank_statement).mapped(
                    "balance"
                )
            )

    def export_bank_statement(self):
        return self.env.ref(
            "bi_bank_statement_reconciliation.action_export_bank_statement_reconciliation"
        ).report_action(self, data={"statement_id": self.id}, config=False)

    def export_bank_statement_pdf(self):
        return self.env.ref(
            "bi_bank_statement_reconciliation.action_export_bank_statement_reco_pdf"
        ).report_action(self, data={"statement_id": self.id}, config=False)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_present_bank_statement = fields.Boolean(
        string="Present in Bank Statement",
        copy=False,
    )
    reference = fields.Char(readonly=False,related="move_id.ref")
    display_amount = fields.Float(string="Amount", store=True)
    display_currency = fields.Char(string="Currency", store=True)
    transaction_date = fields.Date()

    @api.onchange("is_present_bank_statement")
    def set_transaction_date(self):
        self.transaction_date = self.date

    def action_toggle_present_bank_statement(self):
        for record in self:
            record.is_present_bank_statement = not record.is_present_bank_statement

    def action_view_journal_entry(self):
        action = self.env.ref("account.action_move_journal_line").read()[0]
        action.update(
            {
                "views": [(self.env.ref("account.view_move_form").id, "form")],
                "res_id": self.move_id.id,
            }
        )
        return action
