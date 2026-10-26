from odoo import api, models, fields
import logging
import warnings

_logger = logging.getLogger(__name__)


class InvoiceSms(models.Model):
    _inherit = "account.move"

    parent_partner_ids = fields.Many2many(
        "res.partner", string="Parent Partner", compute="_compute_parent_partner"
    )

    @api.depends("partner_id", "state")
    def _compute_parent_partner(self):
        for record in self:
            record.parent_partner_ids = False
            if record.partner_id:
                student_id = self.env["xe.student"].search(
                    [("partner_id", "=", record.partner_id.id)]
                )
                if student_id and student_id.parent_ids:
                    record.parent_partner_ids = [
                        (6, 0, student_id.parent_ids.mapped("partner_id").ids)
                    ]

    def action_post(self):
        result = super(InvoiceSms, self).action_post()
        try:
            email_alert_rec = self.env["xe.send.email.config"].search(
                [("active", "=", True)]
            )
            default_invoice_validate = email_alert_rec.is_email_invoice_validate
            if default_invoice_validate:
                template = email_alert_rec.inv_validate_mail_id
                email = []
                if self.partner_id.email:
                    email.append(self.partner_id.email)
                if self.parent_partner_ids:
                    for parent in self.parent_partner_ids:
                        if parent.email:
                            email.append(parent.email)
                else:
                    student_id = self.env["xe.student"].search(
                        [("partner_id", "=", self.partner_id.id)]
                    )
                    if student_id and student_id.parent_ids:
                        for parent in student_id.parent_ids:
                            email.append(parent.email)
                email = ",".join(email)
                template.with_context(mail=email).send_mail(self.id, force_send=True)
        except Exception as e:
            _logger.info(e)
        return result


class AccountPayments(models.Model):
    _inherit = "account.payment"

    parent_partner_ids = fields.Many2many(
        "res.partner", string="Parent Partner", compute="_compute_parent_partner"
    )

    @api.depends("partner_id", "state")
    def _compute_parent_partner(self):
        for record in self:
            record.parent_partner_ids = False
            if record.partner_id:
                student_id = self.env["xe.student"].search(
                    [("partner_id", "=", record.partner_id.id)]
                )
                if student_id and student_id.parent_ids:
                    record.parent_partner_ids = [
                        (6, 0, student_id.parent_ids.mapped("partner_id").ids)
                    ]

    def action_post(self):
        """draft -> posted"""
        result = super(AccountPayments, self).action_post()
        for rec in self:
            if rec.payment_type == "inbound":
                try:
                    email_alert_rec = self.env["xe.send.email.config"].search(
                        [("active", "=", True)]
                    )
                    default_inv_paid_mail = email_alert_rec.is_email_payment
                    if default_inv_paid_mail:
                        template = email_alert_rec.inv_paid_mail_id
                        email = []
                        if rec.partner_id.email:
                            email.append(rec.partner_id.email)
                        if rec.parent_partner_ids:
                            for parent in rec.parent_partner_ids:
                                if parent.email:
                                    email.append(parent.email)
                        else:
                            student_id = self.env["xe.student"].search(
                                [("partner_id", "=", rec.partner_id.id)]
                            )
                            if student_id and student_id.parent_ids:
                                for parent in student_id.parent_ids:
                                    email.append(parent.email)
                        email = ",".join(email)
                        template.with_context(mail=email).send_mail(
                            rec.id, force_send=True
                        )
                except Exception as e:
                    _logger.info(e)
        return result
