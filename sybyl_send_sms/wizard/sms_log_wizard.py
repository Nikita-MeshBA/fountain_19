from odoo import models, fields


class WizardSmsLog(models.TransientModel):
    _name = "wizard.sms.send.log"
    _description = "Send multiple sms"

    def _get_sms_logs(self):
        if self.env.context and self.env.context.get("active_ids"):
            return self.env.context.get("active_ids")
        return []

    sms_log_ids = fields.Many2many(
        "sms.send.log", default=_get_sms_logs, string="Sms Logs"
    )

    def send_sms_logs(self):
        active_ids = self.env.context.get("active_ids", []) or []
        records = self.env["sms.send.log"].browse(active_ids)
        records.resend_sms()
