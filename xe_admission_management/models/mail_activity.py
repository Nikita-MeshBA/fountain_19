from odoo.exceptions import UserError

from odoo import api, models, _


class MailActivity(models.Model):
    _inherit = "mail.activity"

    @api.model
    def default_get(self, fields):
        result = super(MailActivity, self).default_get(fields)
        is_staff = self.user_has_groups("xenesis_school_base.group_xe_staff")
        if (
            "res_model" in result
            and result["res_model"] == "account.move"
            and not is_staff
        ):
            raise UserError(_("You don't have Access rights to plan Next Activity"))
        return result
