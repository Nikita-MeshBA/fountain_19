from odoo import api, models, fields
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SendEmailVisitor(models.TransientModel):
    _name = "send.email.visitor"

    def _get_active_ids(self):
        active_ids = self._context.get("active_ids")
        return active_ids

    visitor_pass_ids = fields.Many2many(
        "visitor.pass", string="Selected Visitor Records", default=_get_active_ids
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
        for record in self.visitor_pass_ids:
            try:
                template = self.email_template_id
                template.body_html = self.template_body
                email = record.email
                template.with_context(mail=email).send_mail(record.id, force_send=True)
            except Exception as e:
                _logger.info(e)
