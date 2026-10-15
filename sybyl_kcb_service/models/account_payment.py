import logging
from datetime import date, timedelta
from odoo import models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # def _cron_mpesa_payment_creation(self):
    def _cron_kcb_payment_creation(self):
        kcb_trans_ids = (
            self.env["kcb.transaction"]
            .sudo()
            .search(
                [
                    ("state", "=", "draft"),
                    (
                        "dtTransDate",
                        "in",
                        [date.today(), date.today() + timedelta(days=-1)],
                    ),
                ]
            )
        )
        if kcb_trans_ids:
            for kcb in kcb_trans_ids:
                if len(self.env["res.company"].sudo().search([])) > 1:
                    kcb_journal_id = (
                        self.env["account.journal"]
                        .sudo()
                        .search(
                            [
                                ("is_kcb_journal", "=", True),
                                ("company_id", "=", kcb.company_id.id),
                            ],
                            limit=1,
                        )
                    )
                else:
                    kcb_journal_id = (
                        self.env["account.journal"]
                        .sudo()
                        .search([("is_kcb_journal", "=", True)], limit=1)
                    )
                student_id = (
                    self.env["xe.student"]
                    .sudo()
                    .search([("roll_number", "=", kcb.bill_ref_number)], limit=1)
                )
                if student_id and student_id.partner_id:
                    if (
                        len(self.env["res.company"].sudo().search([])) > 1
                        and kcb.company_id.id == student_id.partner_id.company_id.id
                        and not self.env["account.payment"].search(
                            [
                                ("ref", "=", kcb.trans_id),
                                ("company_id", "=", kcb.company_id.id),
                            ]
                        )
                    ):
                        self.create_kcb_payment(kcb, kcb_journal_id, student_id)
                    else:
                        self.create_kcb_payment(kcb, kcb_journal_id, student_id)

    def create_kcb_payment(self, kcb, kcb_journal, student):
        vals = {
            "is_internal_transfer": False,
            "payment_type": "inbound",
            "partner_id": student.partner_id.id if student.partner_id else False,
            "amount": kcb.trans_amount,
            "company_id": student.partner_id.company_id.id,
            "journal_id": kcb_journal.id if kcb_journal else False,
            "state": "draft",
            "ref": kcb.trans_id,
            "payment_method_line_id": kcb_journal.inbound_payment_method_line_ids[0].id
            if kcb_journal.inbound_payment_method_line_ids
            else False,
        }
        try:
            payment_id = self.sudo().create(vals)
            if payment_id:
                kcb.write(
                    {
                        "state": "done",
                        "payment_ids": [(4, payment_id.id)],
                    }
                )
                payment_id.action_post()
        except Exception as e:
            _logger.warning(e)
