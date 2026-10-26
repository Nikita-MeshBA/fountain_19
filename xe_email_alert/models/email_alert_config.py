from odoo.exceptions import UserError
from odoo import models, fields, api, _


class xe_accounting_email(models.Model):
    _name = "xe.send.email.config"
    _description = "Email Configuration for Accounting"

    name = fields.Char(default="Email Alert Configuration")
    active = fields.Boolean(default=True)
    is_email_invoice_validate = fields.Boolean("Invoice Validation")
    is_email_payment = fields.Boolean("Customer Payment")
    is_email_manual = fields.Boolean("Manual Email")
    # old field
    inv_validate_mail = fields.Many2one(
        "mail.template", "Email Template for Invoice Validate"
    )
    # new field
    inv_validate_mail_id = fields.Many2one(
        "mail.template", "Email Template for Invoice Validate"
    )
    # old field
    inv_paid_mail = fields.Many2one(
        "mail.template", "Email Template for Invoice Payment"
    )
    # new field
    inv_paid_mail_id = fields.Many2one(
        "mail.template", "Email Template for Invoice Payment"
    )

    @api.constrains("name")
    def _check_one_active_rec(self):
        for rec in self:
            rec_count = self.env["xe.send.email.config"].search_count(
                [("active", "=", True)]
            )
            if rec_count > 1:
                raise UserError(_("You can set only one active record"))
