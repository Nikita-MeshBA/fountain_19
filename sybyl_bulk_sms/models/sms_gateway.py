import json
import logging

from odoo.exceptions import UserError
from odoo.tools import ustr

from odoo import api, fields, models, _
from ..models.send_sms_api import SENDSMSBase

_logger = logging.getLogger(__name__)


class SmsGatewayConfig(models.Model):
    _name = "sms.gateway.config"
    _description = "SMS Gateway"

    name = fields.Char()
    url = fields.Char("URL")
    property_ids = fields.One2many("sms.gateway.attributes", "gateway_id")
    header_property_ids = fields.One2many("sms.header.attributes", "gateway_id")
    phone_no = fields.Char("Test Phone Number")
    active = fields.Boolean(default=True)
    # old field
    body_property = fields.Many2one(
        "message.property.config",
        "Property name of Message",
    )
    # new field
    body_property_id = fields.Many2one(
        "message.property.config",
        "Property name of Message",
    )
    # old field
    mobile_property = fields.Many2one(
        "mobile.property.config",
        "Property name of Mobile",
    )
    # new field
    mobile_property_id = fields.Many2one(
        "mobile.property.config",
        "Property name of Mobile",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.model
    def default_get(self, fields_list):
        res = super(SmsGatewayConfig, self).default_get(fields_list)
        vals = [
            (0, 0, {"name": "Content-type", "value": "application/json"}),
            (0, 0, {"name": "Accept", "value": "application/json"}),
        ]
        res.update({"header_property_ids": vals})
        return res

    def test_send_sms_connection(self):
        self.ensure_one()
        url = self.url
        values = {}
        header_vals = {}
        for line in self.property_ids:
            if line.name and line.value:
                values[line.name] = line.value
        for line in self.header_property_ids:
            if line.name and line.value:
                header_vals[line.name] = line.value

        values[self.mobile_property_id.name] = self.phone_no
        values[self.body_property_id.name] = self.name
        client = SENDSMSBase(url, self.name)
        try:
            datas = json.dumps(values)
            response = client.test_send_sms(datas, header_vals)
        except Exception as exception:
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(exception)
            )
        if response.status_code == 200:
            _logger.info("Success to send SMS", exc_info=True)
            raise UserError(
                _("Connection Test Succeeded! Everything seems properly set up!")
            )
        else:
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(response)
            )

    @api.model
    def send_sms(self, to_number, body):
        self.ensure_one()
        url = self.url
        values = {}
        header_vals = {}
        for line in self.property_ids:
            if line.name and line.value:
                values[line.name] = line.value
        for line in self.header_property_ids:
            if line.name and line.value:
                header_vals[line.name] = line.value

        client = SENDSMSBase(url, self.name)
        values[self.body_property_id.name] = body
        if not isinstance(to_number, list):
            mobile_numbers = list(to_number.split(","))
        else:
            mobile_numbers = to_number
        state = "Message Sent"
        try:
            for num in mobile_numbers:
                values[self.mobile_property_id.name] = num
                datas = json.dumps(values)
                response = client.test_send_sms(datas, header_vals)
                result = {
                    "to_number": num,
                    "sms_gateway_id": self.id,
                    "template_body": body,
                    "response_status": response.status_code,
                    "response_content": response.content or response.text,
                }
                if response.status_code == 200:
                    result["state"] = "send"
                else:
                    result["state"] = "failed"
                self.env["bulk.sms.send.log"].create(result)
        except:
            state = "Failed to send SMS"
            _logger.warn("Failed to send SMS %s", to_number, exc_info=True)
        return state


class GatewayAttributes(models.Model):
    _name = "sms.gateway.attributes"
    _description = "Gateway Attributes"

    name = fields.Selection(
        [
            ("apiClientID", "apiClientID"),
            ("key", "Auth Key"),
            ("secret", "Auth Secret"),
            ("serviceID", "serviceID"),
            ("apikey", "API Key"),
            ("partnerID", "partnerID"),
            ("shortcode", "Short Code"),
            ("sender", "Sender ID"),
            ("correlator", "Correlator"),
        ],
        string="Property Name",
    )
    value = fields.Char("Property Value")
    gateway_id = fields.Many2one("sms.gateway.config", "Gateway")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )


class HeaderAttributes(models.Model):
    _name = "sms.header.attributes"
    _description = "Header Attributes"

    name = fields.Char("Property Name")
    value = fields.Char("Property Value")
    gateway_id = fields.Many2one("sms.gateway.config", "Gateway")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )


class SendSmsLog(models.Model):
    _name = "bulk.sms.send.log"
    _inherit = ["mail.thread"]
    _description = "SMS Log"

    name = fields.Char(
        default=lambda self: _("New"),
        copy=False,
        string="Message Reference",
        tracking=True,
    )
    to_number = fields.Char()
    template_body = fields.Text(string="Message Body", readonly=True)
    sms_gateway_id = fields.Many2one(
        "sms.gateway.config", string="SMS Gateway", ondelete="restrict", required=True
    )
    response_status = fields.Char("Status of Response")
    response_content = fields.Char("Response Body")
    state = fields.Selection(
        [("failed", "Failed"), ("send", "Sent"), ("cancel", "Cancelled")],
        default="draft",
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.model
    def create(self, vals):
        """Create new Sequence"""
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("sms.send.log") or "New"
        result = super(SendSmsLog, self).create(vals)
        return result
