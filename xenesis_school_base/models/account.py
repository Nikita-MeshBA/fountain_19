from datetime import date, datetime, timedelta
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    course_id = fields.Many2one("xe.course", string="Class")
    class_room_id = fields.Many2one("xe.classroom", string="Classroom")
    terms = fields.Char()
    roll_number = fields.Char(string="Admission Number")
    is_application_invoice = fields.Boolean(readonly=True, store=True)
    display_on_invoice = fields.Boolean(compute="_compute_display_on_invoice")
    total_balance_partner = fields.Monetary(compute="_compute_total_balance_partner")
    grand_total_amount = fields.Monetary(compute="_compute_grand_total_amount")
    pending_invoice_ids = fields.Many2many(
        "account.move",
        "pending_invoice_rel",
        "name",
        compute="_compute_pending_invoice",
    )

    def _cron_reconcile_invoice_payment(self):
        move_ids = (
            self.sudo()
            .search(
                [
                    ("state", "=", "posted"),
                    ("move_type", "in", ["out_invoice", "out_refund"]),
                ],
                order="invoice_date asc",
            )
            .filtered(
                lambda l: datetime.today() + timedelta(days=-1)
                <= l.write_date
                <= datetime.today()
            )
        )
        for move in move_ids:
            domain = [
                (
                    "partner_id",
                    "=",
                    self.env["res.partner"]
                    ._find_accounting_partner(move.partner_id)
                    .id,
                ),
                ("reconciled", "=", False),
                ("move_id.state", "=", "posted"),
                "|",
                "&",
                ("amount_residual_currency", "!=", 0.0),
                ("currency_id", "!=", None),
                "&",
                ("amount_residual_currency", "=", 0.0),
                "&",
                ("currency_id", "=", None),
                ("amount_residual", "!=", 0.0),
            ]

            if move.move_type in ("out_invoice", "in_refund"):
                domain.extend([("credit", ">", 0), ("debit", "=", 0)])
            else:
                domain.extend([("credit", "=", 0), ("debit", ">", 0)])

            lines = (
                self.env["account.move.line"].sudo().search(domain, order="date asc")
            )
            if len(lines) != 0:
                for line in lines:
                    move.js_assign_outstanding_line(line.id)

    def get_account_move_lines(self, partner_ids):
        self.env.cr.execute(
            "SELECT m.name AS move_id, l.date, l.name, l.ref, l.date_maturity, \
            l.partner_id, l.blocked, l.amount_currency, l.currency_id, "
            "CASE WHEN aa.account_type = 'asset_receivable' "
            "THEN SUM(l.debit) "
            "ELSE SUM(l.credit * -1) "
            "END AS debit, "
            "CASE WHEN aa.account_type = 'asset_receivable' "
            "THEN SUM(l.credit) "
            "ELSE SUM(l.debit * -1) "
            "END AS credit, "
            "CASE WHEN l.date_maturity < %s "
            "THEN SUM(l.debit - l.credit) "
            "ELSE 0 "
            "END AS mat "
            "FROM account_move_line l "
            "JOIN account_account aa ON (l.account_id = aa.id) "
            "JOIN account_move m ON (l.move_id = m.id) "
            "WHERE l.partner_id IN %s AND aa.account_type IN ('asset_receivable', 'liability_payable') \
            AND m.state='posted' AND l.full_reconcile_id IS NULL GROUP BY l.date, \
            l.name, l.ref, l.date_maturity, l.partner_id, aa.account_type, l.blocked, \
            l.amount_currency, l.currency_id, l.move_id, m.name",
            ((fields.date.today(),) + (tuple(partner_ids),)),
        )
        result = self.env.cr.dictfetchall()
        return result

    def _partner_balance_new(self, partner_id):
        for rec in self:
            lines = []
            if partner_id:
                lines = rec.get_account_move_lines([partner_id])
            debit = 0
            credit = 0
            for line in lines:
                if line["move_id"]:
                    debit = debit + line["debit"]
                    credit = credit + line["credit"]
            balance = debit - credit
            balance = "%.2f" % round(balance, 2)
            return balance

    def _partner_credit_balance(self, partner_id):
        credit = 0
        for rec in self:
            lines = []
            if partner_id:
                lines = rec.get_account_move_lines([partner_id])

            for line in lines:
                if line["move_id"]:
                    credit = credit + line["credit"]
            balance = credit
            balance = "%.2f" % round(balance, 2)
            return balance

    @api.onchange("partner_id")
    def _set_details(self):
        for line in self:
            if line.partner_id and line.move_type == "out_invoice":
                student = self.env["xe.student"].search(
                    [("partner_id", "=", line.partner_id.id)]
                )
                if student:
                    line.course_id = student.course_id.id
                    line.roll_number = student.roll_number
                    line.class_room_id = student.classroom_id.id

    def _get_line_ids(self):
        record_set = []
        line_ids = self.invoice_line_ids
        ordered_record_set = line_ids.sorted(key=lambda r: r.price_subtotal)
        opening_line = False
        for line in ordered_record_set:
            record_set.append(line)
            if hasattr(line.product_id, "is_opening_blns"):
                opening_line = line
        if opening_line:
            record_set.remove(opening_line)
            record_set.insert(0, opening_line)
        inv_values_array_nofeesreceipt = []
        inv_values_array_withfeesreceipt = []
        total_paid_amount = 0
        total_balance = 0
        fee_receipt_objs = []

        for inv_line in record_set:
            name = inv_line.name
            fee_receipt_id = False

            price_unit = inv_line.price_unit
            amount = inv_line.price_subtotal
            invoice_total_paid = 0
            line_paid_amount = 0
            balance = 0
            invoice_state = inv_line.move_id and inv_line.move_id.state

            if invoice_state not in ("draft", "cancel"):
                invoice_total_paid = (
                    inv_line.move_id.amount_total - inv_line.move_id.amount_residual
                )

            if invoice_state in ("draft", "cancel"):
                invoice_total_paid = 0
            if (
                total_paid_amount + inv_line.price_subtotal
            ) < invoice_total_paid and invoice_state not in ("draft", "cancel"):
                line_paid_amount = inv_line.price_subtotal
                balance = 0
            elif (
                total_paid_amount + inv_line.price_subtotal
            ) >= invoice_total_paid and invoice_state not in ("draft", "cancel"):
                if invoice_total_paid > 0:
                    line_paid_amount = invoice_total_paid - total_paid_amount
                else:
                    line_paid_amount = 0
                if line_paid_amount < 0:
                    line_paid_amount = 0
                    balance = inv_line.move_id.amount_total - total_paid_amount

                else:
                    balance = inv_line.price_subtotal - line_paid_amount
            elif (
                total_paid_amount + inv_line.price_subtotal
            ) >= invoice_total_paid and invoice_state in ("draft", "cancel"):
                line_paid_amount = 0
                balance = inv_line.price_subtotal
            total_paid_amount = total_paid_amount + line_paid_amount
            total_balance = total_balance + balance
            inv_values_dict = {
                "name": name,
                "quantity": 1,
                "price_unit": price_unit,
                "taxes": "",
                "amount": amount,
                "paidamount": line_paid_amount,
                "balance": balance,
            }

            if not fee_receipt_id:
                inv_values_array_nofeesreceipt.append(inv_values_dict)
            else:
                inv_values_dict = {
                    "name": inv_line.name,
                    "quantity": 1,
                    "price_unit": price_unit,
                    "taxes": "",
                    "amount": amount,
                    "paidamount": line_paid_amount,
                    "balance": balance,
                }

                inv_values_array_withfeesreceipt.append(inv_values_dict)
        if inv_values_array_withfeesreceipt:
            inv_values_array_withfeesreceipt = self.get_grouped(
                inv_values_array_withfeesreceipt, fee_receipt_objs
            )
            inv_values_array_withfeesreceipt = [
                dict(t)
                for t in {tuple(d.items()) for d in inv_values_array_withfeesreceipt}
            ]
        final_array = inv_values_array_withfeesreceipt + inv_values_array_nofeesreceipt
        return final_array

    def get_grouped(self, inv_values_array_withfeesreceipt, fee_receipt_objs):
        res = []
        for receipt in fee_receipt_objs:
            name = receipt.name
            price_unit = 0
            amount = 0
            paidamount = 0
            balance = 0
            quantity = 1
            taxes = ""
            for inv_dict in inv_values_array_withfeesreceipt:
                if name == inv_dict["name"]:
                    price_unit = price_unit + inv_dict["price_unit"]
                    amount = amount + inv_dict["amount"]
                    paidamount = paidamount + inv_dict["paidamount"]
                    balance = balance + inv_dict["balance"]

            modified_dict = {
                "name": name,
                "quantity": quantity,
                "price_unit": price_unit,
                "taxes": taxes,
                "amount": amount,
                "paidamount": paidamount,
                "balance": balance,
            }
            res.append(modified_dict)
        return res

    @api.model
    def create(self, vals):
        if vals.get("partner_id") and not vals.get("roll_number"):
            student = self.env["xe.student"].search(
                [("partner_id", "=", vals.get("partner_id"))]
            )
            if student:
                vals["course_id"] = student.course_id.id or False
                vals["roll_number"] = student.roll_number or False
                vals["class_room_id"] = student.classroom_id.id or False
        return super(AccountMove, self).create(vals)

    @api.depends("partner_id")
    def _compute_total_balance_partner(self):
        for rec in self:
            if rec.partner_id:
                for invoice in rec.pending_invoice_ids:
                    rec.total_balance_partner += invoice.amount_residual
                rec.grand_total_amount = rec.amount_residual + rec.total_balance_partner
            else:
                rec.total_balance_partner = 0
                rec.grand_total_amount = rec.amount_residual + rec.total_balance_partner

    @api.depends("amount_residual", "total_balance_partner")
    def _compute_grand_total_amount(self):
        for rec in self:
            rec.grand_total_amount = rec.amount_residual + rec.total_balance_partner

    @api.depends("partner_id")
    def _compute_pending_invoice(self):
        for rec in self:
            if rec.partner_id:
                if bool(rec.id):
                    account_move_ids = self.search(
                        [
                            ("id", "!=", rec.id),
                            ("partner_id", "=", rec.partner_id.id),
                            ("state", "=", "posted"),
                            ("payment_state", "in", ["partial", "not_paid"]),
                        ]
                    )
                else:
                    account_move_ids = self.search(
                        [
                            ("partner_id", "=", rec.partner_id.id),
                            ("state", "=", "posted"),
                            ("payment_state", "in", ["partial", "not_paid"]),
                        ]
                    )
                rec.pending_invoice_ids = [(6, 0, account_move_ids.ids)]
            else:
                rec.pending_invoice_ids = [(6, 0, [])]

    def _compute_display_on_invoice(self):
        display_on_invoice = (
            self.env["ir.config_parameter"].sudo().get_param("balance_on_invoice")
            or False
        )
        for rec in self:
            if bool(display_on_invoice):
                rec.display_on_invoice = True
            else:
                rec.display_on_invoice = False
