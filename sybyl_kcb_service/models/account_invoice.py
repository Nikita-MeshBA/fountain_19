# pylint: disable=E0401
from odoo import models, fields, _


class AccountInvoice(models.Model):
    _inherit = "account.move"

    bill_ref_no = fields.Char()

    def button_kcb_cash_entries(self):
        return {
            "name": _("KCB Transaction"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "kcb.transaction",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("move_id", "in", self.ids)],
        }

    def make_kcb_register(self, line, account_journal, method_line_id):
        vals = {
            "amount": line.dblAmount,
            "partner_type": "customer",
            "payment_date": line.dtTransDate,
            "communication": self.name,
            "journal_id": account_journal[0].id,
            # 'hide_payment_method': True,
            "payment_method_line_id": method_line_id.id,
        }
        register_payments = (
            self.env["account.payment.register"]
            .with_context({"active_ids": self.ids, "active_model": "account.move"})
            .create(vals)
        )
        payments = register_payments._create_payments()
        # Payment = self.env['account.payment']
        # payments = Payment
        # for payment_vals in :
        #     payments += Payment.create(payment_vals)
        # payments.post()
        line.write(
            {"state": "done", "move_id": self.id, "payment_ids": [(6, 0, payments.ids)]}
        )
