import logging
from datetime import date, timedelta
from odoo import models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _cron_mpesa_payment_creation(self):
        mpesa_trans_ids = (
            self.env["mpesa.payment.transaction"]
            .sudo()
            .search(
                [
                    ("state", "=", "draft"),
                    ("date", "in", [date.today(), date.today() + timedelta(days=-1)]),
                ]
            )
        )
        if mpesa_trans_ids:
            for mpesa in mpesa_trans_ids:
                if len(self.env["res.company"].sudo().search([])) > 1:
                    mpesa_journal_id = (
                        self.env["account.journal"]
                        .sudo()
                        .search(
                            [
                                ("is_mpesa_journal", "=", True),
                                ("company_id", "=", mpesa.company_id.id),
                            ], limit=1
                        )
                    )
                else:
                    mpesa_journal_id = (
                        self.env["account.journal"]
                        .sudo()
                        .search([("is_mpesa_journal", "=", True)], limit=1)
                    )
                student_id = (
                    self.env["xe.student"]
                    .sudo()
                    .search([("roll_number", "=", mpesa.bill_ref_number)], limit=1)
                )
                if student_id and student_id.partner_id:
                    if (
                        len(self.env["res.company"].sudo().search([])) > 1
                        and mpesa.company_id.id == student_id.partner_id.company_id.id
                        and not self.env["account.payment"].search(
                            [
                                ("ref", "=", mpesa.trans_id),
                                ("company_id", "=", mpesa.company_id.id),
                            ]
                        )
                    ):
                        self.create_mpesa_payment(mpesa, mpesa_journal_id, student_id)
                    else:
                        self.create_mpesa_payment(mpesa, mpesa_journal_id, student_id)

    def create_mpesa_payment(self, mpesa, mpesa_journal, student):
        vals = {
            "is_internal_transfer": False,
            "payment_type": "inbound",
            "partner_id": student.partner_id.id if student.partner_id else False,
            "amount": mpesa.trans_amount,
            "company_id": student.partner_id.company_id.id,
            "journal_id": mpesa_journal.id if mpesa_journal else False,
            "state": "draft",
            "ref": mpesa.trans_id,
            "payment_method_line_id": mpesa_journal.inbound_payment_method_line_ids[
                0
            ].id
            if mpesa_journal.inbound_payment_method_line_ids
            else False,
        }
        try:
            payment_id = self.sudo().create(vals)
            if payment_id:
                mpesa.write(
                    {
                        "state": "done",
                        "payment_ids": [(4, payment_id.id)],
                    }
                )
                payment_id.action_post()
        except Exception as e:
            _logger.warning(e)