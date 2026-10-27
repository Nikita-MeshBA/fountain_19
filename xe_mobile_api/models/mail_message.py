""" Mail Message python file """
# pylint: disable= E0401, C0116, R0903
from odoo import models, api, fields, _


class Message(models.Model):
    """Mail Message inherit class"""

    _inherit = "mail.message"

    channel_ids = fields.Many2many(
        string="Channels",
        comodel_name="discuss.channel",
        relation="mail_channel_message",
        column1="message_id",
        column2="channel_id",
        copy=False,
    )

    # @api.model
    # def create(self, values):
    #     res = super(Message, self).create(values)
    #     partners = self.env["res.partner"]
    #     if values.get("message_type") == "comment":
    #         partner = self.env.user.partner_id
    #         title = _("New message from %s") % (partner.name)
    #         body = values.get("body", "")
    #         if res.model == "discuss.channel":
    #             channel_id = res.res_id
    #             channel = self.env["discuss.channel"].browse(channel_id)
    #             if channel.channel_type in ["chat", "channel"]:
    #                 partners = channel.channel_partner_ids.filtered(
    #                     lambda p: p.id != partner.id
    #                 )
    #     if partners:
    #         partners.do_notify_firebase(title, body, res.id, channel.id)
    #     return res
    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)

        for values, message in zip(vals_list, messages):
            if values.get("message_type") != "comment":
                continue

            partner = self.env.user.partner_id
            title = _("New message from %s") % partner.name
            body = values.get("body", "")

            if message.model != "discuss.channel":
                continue

            channel = self.env["discuss.channel"].browse(message.res_id)

            if channel.channel_type in ["chat", "channel"]:
                partners = channel.channel_partner_ids.filtered(
                    lambda p: p.id != partner.id
                )

                if partners:
                    partners.do_notify_firebase(
                        title, body, message.id, channel.id
                    )

        return messages