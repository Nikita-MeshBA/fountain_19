# pylint: disable=E0401,C0114,C0115,C0116
from odoo import models, fields, _


class AccountInvoice(models.Model):
    _inherit = "account.move"

    reg_payment = fields.Float("Register Payment")

    def button_dtb_cash_entries(self):
        return {
            "name": _("DTB Transaction"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "dtb.transaction",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("move_id", "in", self.ids)],
        }

    def make_dtb_register(self, line, account_journal, method_line_id):
        vals = {
            "amount": line.dblAmount,
            "partner_type": "customer",
            "payment_date": line.dtTransDate,
            "communication": line.narration,
            "journal_id": account_journal[0].id,
            # 'hide_payment_method': True,
            "payment_method_line_id": method_line_id.id,
        }
        if line.debit_credit_indicator == "D":
            vals["partner_type"] = "supplier"
        register_payments = (
            self.env["account.payment.register"]
            .with_context({"active_ids": self.ids, "active_model": "account.move"})
            .create(vals)
        )
        payments = register_payments._create_payments()
        line.write(
            {
                "state": "done",
                "move_id": self.id,
                "move_ids": [(6, 0, self.ids)],
                "payment_ids": [(6, 0, payments.ids)],
            }
        )
