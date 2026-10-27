""" Discuss APIs python file """
# pylint: disable= E0401, C0116, R0801
import lxml
import json
import datetime
from odoo import http
from odoo.http import request
from ..controllers.main import set_offset_limit

from markupsafe import Markup
from werkzeug.exceptions import NotFound
from odoo.addons.mail.controllers.thread import ThreadController
from odoo.addons.mail.tools.discuss import add_guest_to_context

class DiscussApi(http.Controller):
    """Discuss APIs"""

    @http.route("/discuss/details", type="json", auth="user")
    def get_discuss_details(self, **kw):
        partner_id = request.env.user and request.env.user.partner_id and request.env.user.partner_id.id or False
        offset, limit = set_offset_limit(kw)
        domain = [("channel_partner_ids", "in", [partner_id])]
        if kw.get("type", False):
            domain += [("channel_type", "=", kw.get("type"))]
        if kw.get("searchby", False):
            domain += [("name", "ilike", kw.get("searchby"))]

        channel_ids = request.env["discuss.channel"].sudo().search_read(domain, ["name", "channel_partner_ids"], offset=offset, limit=limit)
        if kw.get("type") == "channel":
            return channel_ids
        if kw.get("type") == "chat":
            new_channel_ids = []
            for chl in channel_ids:
                member = request.env['discuss.channel.member'].sudo().search([('partner_id', '=', partner_id), ('channel_id', '=', chl["id"]), ('is_pinned', '=', False)])
                if not member:
                    new_channel_ids.append(chl)

            for channel in new_channel_ids:
                if partner_id:
                    channel["channel_partner_ids"].remove(partner_id)
                channel["name"] = request.env["res.partner"].sudo().browse(channel["channel_partner_ids"]).name or "OdooBot"

            for channel in new_channel_ids:
                channel.pop("channel_partner_ids")
            return new_channel_ids

    @http.route("/discuss/pinned_messages", type="json", auth="user")
    def set_discuss_pinned_messages(self, **kw):
        channel_id = kw.get("channel_id")
        message_id = kw.get("message_id")
        pinned = kw.get("pinned")
        if pinned == 1:
            pinned = bool(1)
        elif pinned == 0:
            pinned = bool(0)

        message = request.env["discuss.channel"].sudo().browse(channel_id).set_message_pin(message_id, pinned)
        return True

    @http.route("/discuss/search/chat/partner", type="json", auth="user")
    def set_discuss_chat_search_partner(self, **kw):
        partner = request.env["res.partner"].sudo().im_search(kw.get("searchby"))
        return partner

    @http.route("/discuss/channel/all/messages", type="json", auth="user")
    def get_discuss_channel_all_messages(self, **kw):
        offset, limit = set_offset_limit(kw)
        domain = [
            ("res_id", "=", kw.get("channel_id")),
            ("model", "=", "discuss.channel"),
            ("message_type", "!=", "user_notification"),
        ]
        res = request.env["mail.message"].sudo().search_read(domain,
            ["id", "date", "body", "attachment_ids", "model", "record_name",
            "message_type", "email_from", "author_id", "author_avatar", "create_date", "write_date"],
            offset=offset, limit=limit, order="id desc")
        for msg in res:
            if msg.get("body"):
                msg["body"] = lxml.html.fromstring(msg["body"]).text_content()
            if msg.get("attachment_ids"):
                attachments = []
                for attachment in msg.get("attachment_ids"):
                    attachment_id = request.env["ir.attachment"].sudo().browse(attachment)
                    attachments.append({
                        "id": attachment,
                        "name": attachment_id.name
                })
                msg["attachment_ids"] = attachments
        return res

    @http.route("/discuss/chat/pin", type="json", auth="user")
    def set_discuss_chat_pin(self, **kw):
        channel_id = request.env["discuss.channel"].sudo().browse(kw.get("channel_id")).channel_pin(pinned=False)
        return True

    @http.route("/discuss/channel/pin", type="json", auth="user")
    def set_discuss_channel_pin(self, **kw):
        channel_id = request.env["discuss.channel"].sudo().browse(kw.get("channel_id")).action_unfollow()
        return True

    @http.route("/discuss/create/chat", type="json", auth="user")
    def discuss_create_chat(self, **kw):
        partner_id = request.env["res.partner"].sudo().browse(kw.get("partner_id"))
        channel = request.env["discuss.channel"].sudo().channel_get(partners_to=[kw.get("partner_id")])
        if channel:
            return {
                "id": channel.id,
                "name": partner_id.name,
            }
        return {"message": "Chat not created."}


class DiscusschatThreadController(ThreadController):

    @http.route("/mail/message/update_content", methods=["POST"], type="json", auth="public")
    @add_guest_to_context
    def mail_message_update_content(self, message_id, body, attachment_ids, attachment_tokens=None, partner_ids=None, mobile=False):
        guest = request.env["mail.guest"]._get_guest_from_context()
        guest.env["ir.attachment"].browse(attachment_ids)._check_attachments_access(attachment_tokens)
        message_sudo = guest.env["mail.message"].browse(message_id).sudo().exists()
        if not message_sudo.is_current_user_or_guest_author and not guest.env.user._is_admin():
            raise NotFound()
        if not message_sudo.model or not message_sudo.res_id:
            raise NotFound()
        body = Markup(body) if body else body  # may contain HTML such as @mentions
        guest.env[message_sudo.model].browse([message_sudo.res_id])._message_update_content(
            message_sudo, body, attachment_ids=attachment_ids, partner_ids=partner_ids
        )
        if not mobile:
            return message_sudo.message_format()[0]
        if mobile and body:
            return message_sudo.message_format()[0]
        if mobile and not body:
            message_sudo.unlink()
            return []
        return message_sudo.message_format()[0]
