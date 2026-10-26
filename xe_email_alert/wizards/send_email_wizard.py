from odoo.exceptions import UserError
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class SendEmailWizard(models.TransientModel):
    _name = "send.email.wizard"

    def _get_active_invoices(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    invoice_ids = fields.Many2many(
        "account.move", string="Invoices", default=_get_active_invoices
    )
    email_template_id = fields.Many2one("mail.template", string="Send Email Template")
    template_body = fields.Text("Body", translate=True, help="Plain text of message")

    @api.onchange("email_template_id")
    def _set_template_body(self):
        if self.email_template_id:
            self.template_body = False
            self.template_body = self.email_template_id.body_html

    def action_send_mail(self):
        email_alert_rec = self.env["xe.send.email.config"].search(
            [("active", "=", True)]
        )
        default_invoice_manual = email_alert_rec.is_email_manual
        if default_invoice_manual:
            for invoice in self.invoice_ids:
                try:
                    template = self.email_template_id
                    template.body_html = self.template_body
                    email = []
                    if invoice.partner_id.email:
                        email.append(invoice.partner_id.email)
                    if invoice.parent_partner_ids:
                        for parent in invoice.parent_partner_ids:
                            if parent.email:
                                email.append(parent.email)
                    else:
                        student_id = self.env["xe.student"].search(
                            [("partner_id", "=", invoice.partner_id.id)]
                        )
                        if student_id and student_id.parent_ids:
                            for parent in student_id.parent_ids:
                                email.append(parent.email)
                    email = ",".join(email)
                    template.with_context(mail=email).send_mail(
                        invoice.id, force_send=True
                    )
                except Exception as e:
                    _logger.info(e)
        else:
            raise UserError(_("Sorry you cant send manual email !!"))
