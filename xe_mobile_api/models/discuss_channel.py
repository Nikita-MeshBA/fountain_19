""" Discuss Channel python file """
# pylint: disable= E0401, R0903
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class Channel(models.Model):
    """Discuss Channel inherit class"""

    _inherit = "discuss.channel"

    def get_last_channel_fetch_message(self, partner_id=False, limit=20):
        """Return message values of the current channel.
        :param partner_id : author id to start the research
        :param limit : maximum number of messages to fetch
        :returns list of messages values
        :rtype : list(dict)
        """
        self.ensure_one()

        domain = [("id", "in", self.sudo().message_ids.ids)]
        if partner_id:
            domain.append(("author_id", "=", partner_id))
        return (
            self.env["mail.message"].sudo()._message_fetch(domain=domain, limit=limit)
        )
