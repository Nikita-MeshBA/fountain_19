""" Assignment python file """
# pylint: disable= E0401, C0116, R0903
from odoo import models, _


class Assignment(models.Model):
    """Assignment inherit class"""

    _inherit = "xe.assignment"

    def act_publish(self):
        res = super(Assignment, self).act_publish()
        partners = self.allocation_ids.mapped("partner_id")
        channel_id = ""
        title = _("Received Assignment from %s") % self.faculty_id.name
        body = _(self.name)
        if partners:
            partners.do_notify_firebase(title, body, self.id, channel_id)
        return res
