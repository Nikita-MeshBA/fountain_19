from odoo.exceptions import UserError

from odoo import models, _


class ValidateAccountMove(models.TransientModel):
    _inherit = "validate.account.move"

    def validate_move(self):
        if self._context.get("active_model") == "account.move":
            domain = [
                ("id", "in", self._context.get("active_ids", [])),
                ("state", "=", "draft"),
            ]
        elif self._context.get("active_model") == "account.journal":
            domain = [
                ("journal_id", "=", self._context.get("active_id")),
                ("state", "=", "draft"),
            ]
        else:
            raise UserError(_("Missing 'active_model' in context."))

        moves = self.env["account.move"].search(domain).filtered("line_ids")
        if not moves:
            raise UserError(_("There are no journal items in the draft state to post."))
        moves._post(not self.force_post)
        for move in moves:
            if move.move_type == "out_invoice":
                sms_alert_rec = self.env["xe.send.sms.config"].search(
                    [("active", "=", True)]
                )
                default_invoice_validate = sms_alert_rec.is_invoice_validate
                if default_invoice_validate:
                    template = sms_alert_rec.invoice_validate_tmpl_id
                    send_sms_template = self.env["send.sms.template"]
                    send_sms_template.send_sms(template.id, move.id)
        return {"type": "ir.actions.act_window_close"}
