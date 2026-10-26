import json
import logging
from odoo.tools import ustr
from datetime import datetime
from odoo.http import request
from odoo.exceptions import UserError
from ..models.send_sms_api import SENDSMSBase
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class SmsGateway(models.Model):
    _name = "sms.gateway"
    _description = "SMS Gateway"

    name = fields.Char(string="Gateway Name", required=True)
    apiClientID = fields.Char(string="Account Name", required=True)
    key = fields.Char(string="Token", required=True)
    secret = fields.Char(required=True)
    serviceID = fields.Char(string="Service ID")
    active = fields.Boolean(default=True)
    txtMessage = fields.Char(string="Test txtMessage", required=True)
    Msisdn = fields.Char(string="Test MSISDN (From Number)")

    def test_send_sms_connection(self):
        self.ensure_one()
        ACCOUNT_SID = self.apiClientID
        KEY = self.key
        SECRET = self.secret
        SERVICEID = self.serviceID
        txt_message = self.txtMessage
        msisdn = self.Msisdn
        client = SENDSMSBase(ACCOUNT_SID, KEY, SECRET, SERVICEID, txt_message, msisdn)
        try:
            response = client.test_send_sms()
        except Exception as exception:
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(exception)
            )
        res = response.json()
        if res and res.get("status") == 222:
            _logger.info("Success to send SMS %s", self.Msisdn, exc_info=True)
            raise UserError(
                _("Connection Test Succeeded! Everything seems properly set up!")
            )
        elif res.get("code") == 2:
            error_str = (
                "Status Code:- "
                + str(res["code"])
                + "\n Status Message:- "
                + res["message"]
            )
            _logger.warning("Failed to send SMS %s", self.Msisdn, exc_info=True)
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(error_str)
            )
        else:
            error_str = (
                "Status Code:- "
                + str(res["status"])
                + "\n Status Message:- "
                + res["status_message"]
            )
            _logger.warning("Failed to send SMS %s", self.Msisdn, exc_info=True)
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(error_str)
            )

    @api.model
    def send_sms(self, to_number, body, model, record_id, template_id):
        ACCOUNT_SID = self.apiClientID
        KEY = self.key
        SECRET = self.secret
        SERVICEID = self.serviceID
        mobile_numbers = list(to_number.split(","))
        for num in mobile_numbers:
            client = SENDSMSBase(ACCOUNT_SID, KEY, SECRET, SERVICEID, body, num)
            res = {}

            try:
                response = client.send_sms(body=body, to_number=num)
                res = response.json()
            except:
                _logger.warning("Failed to send SMS %s", num, exc_info=True)

            if res and res.get("status") == 222:
                _logger.info("Success to send SMS %s", num, exc_info=True)
            elif res.get("code") == 2:
                error_str = (
                    "Status Code:- "
                    + str(res["code"])
                    + "\n Status Message:- "
                    + res["message"]
                )
                _logger.warning("Failed to send SMS %s", self.Msisdn, exc_info=True)
                raise UserError(
                    _("Connection Test Failed! Here is what we got instead:\n %s")
                    % ustr(error_str)
                )
            else:
                error_str = (
                    "Status Code:- "
                    + str(res.get("status", "404"))
                    + "\n Status Message:- "
                    + res.get("status_message", "Connection issue")
                )
                _logger.warning(
                    "Failed to send SMS %s %s", self.Msisdn, error_str, exc_info=True
                )
                result = {
                    "error_code": str(res.get("status", "404")),
                    "error_message": res.get("status_message", "Connection issue"),
                    "sms_gateway_id": self.id,
                    "to_number": num,
                    "template_body": body,
                    "model": model,
                    "record_id": record_id,
                    "sms_template_id": int(template_id),
                }
                self.env["sms.send.log"].create(result)

    @api.model
    def resend_sms(self, to_number, body, error_log):
        ACCOUNT_SID = self.apiClientID
        KEY = self.key
        SECRET = self.secret
        SERVICEID = self.serviceID
        client = SENDSMSBase(ACCOUNT_SID, KEY, SECRET, SERVICEID, body, to_number)
        try:
            response = client.send_sms(body=body, to_number=to_number)
            error_log.send_state()
        except Exception as exception:
            return exception
        return response


class SendSmsLog(models.Model):
    _name = "sms.send.log"
    _description = "SMS Log"

    name = fields.Char(
        default=lambda self: _("New"),
        copy=False,
        readonly=True,
        required=True,
        index=True,
        string="Message Reference",
    )
    error_code = fields.Char(readonly=True, index=True)
    error_message = fields.Text(readonly=True)
    to_number = fields.Char()
    template_body = fields.Text(string="Message Body", readonly=True)
    model = fields.Char(string="Model Name", readonly=True)
    record_id = fields.Char(string="Record Reference", readonly=True)
    sms_gateway_id = fields.Many2one(
        "sms.gateway", string="SMS Gateway", ondelete="restrict", required=True
    )
    sms_template_id = fields.Many2one(
        "send.sms.template", string="SMS Template", required=True
    )
    state = fields.Selection(
        [("draft", "Draft"), ("send", "Send"), ("cancel", "Cancelled")], default="draft"
    )

    @api.model
    def create(self, vals):
        """Create new Sequence"""
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("sms.send.log") or "New"
        result = super(SendSmsLog, self).create(vals)
        return result

    def cancel_state(self):
        self.ensure_one()
        self.write({"state": "cancel"})

    def send_state(self):
        self.ensure_one()
        self.write({"state": "send"})

    def resend_sms(self):
        for record in self:
            template = record.sms_template_id
            send_sms_template = self.env["send.sms.template"]
            if template and template.active:
                sms_rendered_content = send_sms_template.render_template(
                    template.template_body,
                    template.model_id.model,
                    int(record.record_id),
                )
                rendered_msg_to = record.to_number or ""
                gateway_model = template.sms_account_gateway_id
                if gateway_model:
                    result = gateway_model.resend_sms(
                        rendered_msg_to, sms_rendered_content, record
                    )
                    res = result.json()
                    if res and res.get("status") != 222:
                        error_str = (
                            "Status Code:- "
                            + str(res.get("status", "404"))
                            + "\n Status Message:- "
                            + res.get("status_message", "Connection issue")
                        )
                        _logger.warning(
                            "Failed to send SMS %s %s",
                            rendered_msg_to,
                            error_str,
                            exc_info=True,
                        )
                        raise UserError(
                            _('Failed to send SMS "%s"')
                            % (res.get("status_message", "Connection issue"),)
                        )
            else:
                raise UserError(_("Gateway not defined in SMS Template"))
