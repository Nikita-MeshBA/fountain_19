""" Partner python file """
# pylint: disable= E0401, R0903, C0116
import logging
from odoo import models, fields
from ..models.firebase_notification import FireBaseNotificationBase

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Partner inherit class"""

    _inherit = "res.partner"

    firebase_token = fields.Char(string="Push Notification Token")

    def do_notify_firebase(self, title, body, message_id, channel_id):
        server_url = (
            self.env["ir.config_parameter"].sudo().get_param("api.firebase.url")
        )
        server_token = (
            self.env["ir.config_parameter"].sudo().get_param("api.firebase.token")
        )
        sender_partner = self.env.user.partner_id
        notification = FireBaseNotificationBase(server_url, server_token)
        _logger.info("____________________inside partner notify___________________")
        _logger.info(notification)
        for partner in self.filtered(lambda p: p.firebase_token):
            _logger.info(
                "_____________________________partner firebase token_________________"
            )
            _logger.info(partner.firebase_token)
            notification.send_notification(
                title,
                body,
                partner.firebase_token,
                message_id,
                channel_id,
                partner.id,
                sender_partner.id,
            )
