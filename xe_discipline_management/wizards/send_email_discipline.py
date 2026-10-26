from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SendEmailDiscipline(models.TransientModel):
    _name = "send.email.discipline"

    def _get_active_ids(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    discipline_records_ids = fields.Many2many(
        "xe.discipline.records", string="Discipline Records", default=_get_active_ids
    )
    email_template_id = fields.Many2one(
        "mail.template", string="Send Email Template", required=True
    )
    template_body = fields.Text("Body", translate=True, help="Plain text of message")
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")

    @api.onchange("email_template_id")
    def _set_template_body(self):
        if self.email_template_id:
            self.template_body = False
            self.template_body = self.email_template_id.body_html

    def action_send_email(self):
        for record in self.discipline_records_ids:
            try:
                email_to = record.student_id.email if record.student_id.email else ""
                for parent in record.student_id.parent_ids:
                    if email_to:
                        if parent.email:
                            email_to += ",%s" % (parent.email)
                    else:
                        if parent.email:
                            email_to += "%s" % (parent.email)
                template = self.email_template_id
                template.body_html = self.template_body
                template.email_to = email_to
                email = record.student_id.email

                if template.attachment_ids:
                    template.attachment_ids = False
                if self.attachment_ids:
                    template.attachment_ids = [(6, 0, self.attachment_ids.ids)]
                template.with_context(mail=email).send_mail(record.id, force_send=True)
            except Exception as e:
                _logger.info(e)
