from odoo import api, models, fields


class InvoiceReceiptReport(models.AbstractModel):
    _name = "report.sybyl_invoice_receipt_resize.print_invoice_receipt"

    def _get_report_values(self, docids, data):
        docs = self.env.context.get("active_ids")
        if docs == None:
            docs = docids
        return {
            "docs": docs,
            "datas": self.env["account.move"].search(
                [("id", "in", docs), ("move_type", "=", "out_invoice")]
            ),
        }


class AccountMove(models.Model):
    _inherit = "account.move"

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
            partner_id = rec.partner_id and rec.partner_id.id or False
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
            return balance
