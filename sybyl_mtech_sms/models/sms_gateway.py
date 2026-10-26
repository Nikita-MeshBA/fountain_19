# -*- coding: utf-8 -*-
import json
import uuid
import logging
import requests
from odoo.tools import ustr
from odoo.exceptions import UserError
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)
header = {
    "Content-type": "application/json",
    "Accept": "application/json",
}


class SmsGatewayConfigInherit(models.Model):
    _inherit = "sms.gateway.config"
    _description = "SMS Gateway"

    is_mtech_sms = fields.Boolean(default=False)
    mtech_user_name = fields.Char("API Username")
    mtech_password = fields.Char("API Key")
    mtech_balance = fields.Float()
    auth_url = fields.Char("Auth URL")
    callback_url = fields.Char("Callback URL")
    auth_token = fields.Char("Authentication Token")
    sender_id = fields.Char("Sender")

    @api.onchange("is_mtech_sms")
    def _onchange_is_mtech_sms(self):
        if self.is_mtech_sms:
            self.url = "https://api.mtechcomm.co.ke/index.php/messaging/send"
            self.auth_url = "https://api.mtechcomm.co.ke/index.php/auth/token"
        if not self.is_mtech_sms:
            self.url = ""
            self.auth_url = ""

    def test_send_sms_connection(self):
        if self.is_mtech_sms:
            self.mtech_test_send_sms_connection()
        else:
            super(SmsGatewayConfigInherit, self).test_send_sms_connection()

    def mtech_test_send_sms_connection(self):
        self.ensure_one()
        auth_url = self.auth_url
        user_name = self.mtech_user_name
        password = self.mtech_password
        # Get Authentication Token
        values = {"username": user_name, "password": password}
        try:
            auth_response = requests.post(
                url=auth_url, headers=header, data=json.dumps(values)
            )
        except Exception as exception:
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(exception)
            )
        auth_res = auth_response.json()

        if auth_res.get("status", False) == 200:
            _logger.info("Connected Successfully", exc_info=True)
            self.auth_token = auth_res["data"]["token"]

            # Connection Success Message
            try:
                response = self.mtech_sms(
                    body="Successfully SMS Gateway Connected - %s" % (self.name),
                    to_number=self.phone_no,
                    record_id=False,
                    callback_url=self.callback_url,
                    user_name=self.mtech_user_name,
                    password=self.mtech_password,
                )
            except Exception as exception:
                raise UserError(
                    _("Connection Test Failed! Here is what we got instead:\n %s")
                    % ustr(exception)
                )
            res = response.json()
            _logger.info("%s", res)
            if res.get("status") == 200:
                _logger.info("Sucess to send SMS", exc_info=True)
            else:
                err_message = res
                error_str = "Status Message:- " + str(err_message)
                _logger.warn("Failed to send SMS", exc_info=True)
                raise UserError(
                    _("Connection Test Failed! Here is what we got instead:\n %s")
                    % ustr(error_str)
                )
        else:
            raise UserError(str(auth_res))

    def mtech_send_sms(self, to_number, body, model, record_id, template_id):
        res = {}
        try:
            for num in to_number:
                if num:
                    response = self.mtech_sms(
                        body=body,
                        to_number=num,
                        record_id=record_id,
                        callback_url=self.callback_url,
                        user_name=self.mtech_user_name,
                        password=self.mtech_password,
                    )
                    res = response.json()
                    _logger.info("Response %s", res)
                    if res.get("status") == 200:
                        _logger.info("Sucess to send SMS", exc_info=True)
                        result = {
                            "to_number": num,
                            "template_body": body,
                            "sms_gateway_id": self.id,
                            "response_status": res.get("message"),
                            "response_content": res,
                            "state": "send",
                            "company_id": self.env.company.id,
                        }
                        self.env["bulk.sms.send.log"].create(result)
                    else:
                        _logger.warn("Failed to send SMS", exc_info=True)
                        result = {
                            "to_number": num,
                            "template_body": body,
                            "sms_gateway_id": self.id,
                            "response_status": res.get("message"),
                            "response_content": res,
                            "state": "failed",
                            "company_id": self.env.company.id,
                        }
                        res = self.env["bulk.sms.send.log"].create(result)
                        _logger.warn("Failed to send SMS", exc_info=True)
        except:
            _logger.warn("Failed to send SMS %s", to_number, exc_info=True)

    def mtech_sms(self, body, to_number, record_id, callback_url, user_name, password):
        auth_url = self.auth_url
        auth_token = self.auth_token
        # Get Authentication Token
        values = {"username": user_name, "password": password}
        try:
            auth_response = requests.post(
                url=auth_url, headers=header, data=json.dumps(values)
            )
            auth_res = auth_response.json()
            if auth_res["status"] == 200:
                auth_token = auth_res["data"]["token"]
            else:
                response = auth_res
        except Exception as exception:
            response = exception

        uid = uuid.uuid4()
        message_id = uid.hex
        header["Authorization"] = "Bearer " + auth_token
        values = {
            "message": body,
            "sender": self.sender_id,
            "message_type": "Transactional",
            "dlr_url": callback_url,
            "msisdns": [to_number],
            "message_id": message_id,
        }
        response = requests.post(url=self.url, headers=header, data=json.dumps(values))
        return response

    def button_mtech_balance(self):
        url = "https://api.mtechcomm.co.ke/index.php/messaging/balance"
        auth_url = self.auth_url
        auth_token = self.auth_token
        user_name = self.mtech_user_name
        password = self.mtech_password
        # Get Authentication Token
        values = {"username": user_name, "password": password}
        try:
            auth_response = requests.post(
                url=auth_url, headers=header, data=json.dumps(values)
            )
            auth_res = auth_response.json()
            if auth_res["status"] == 200:
                auth_token = auth_res["data"]["token"]
        except Exception as exception:
            _logger.info(exception, exc_info=True)

        header["Authorization"] = "Bearer " + auth_token
        try:
            balance_response = requests.post(
                url=url, headers=header, data=json.dumps(values)
            )
        except Exception as exception:
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(exception)
            )
        balance_res = balance_response.json()

        if balance_res.get("status") == 200:
            self.mtech_balance = float(balance_res["data"]["balance"])
            _logger.info("Balance updated", exc_info=True)
        else:
            _logger.warn("Balance not updated", exc_info=True)
            raise UserError(_("Mtech balance not update."))


class SmsTemplateInherit(models.TransientModel):
    _inherit = "send.sms.template.new"

    def send_sms_new(self):
        gateway_model = self.sms_account_gateway
        if gateway_model:
            emp_mobiles = []
            if self.filter_by == "employee":
                if self.emp_send_by == "department":
                    for dept in self.department_ids:
                        dpt_mobiles = dept.member_ids.mapped("mobile_phone")
                        if dpt_mobiles:
                            emp_mobiles.extend(dpt_mobiles)
                else:
                    if self.employee_ids:
                        emp_mobs = self.employee_ids.mapped("mobile_phone")
                        emp_mobiles.extend(emp_mobs)
            elif self.filter_by == "student":
                parents = self.env["xe.parent"].search(
                    [("student_ids", "in", self.student_ids.ids)]
                )
                parent_mobiles = parents.mapped("mobile")
                if parent_mobiles:
                    emp_mobiles.extend(parent_mobiles)
                if self.student_ids:
                    student_mobile = self.student_ids.mapped("mobile")
                    if student_mobile:
                        emp_mobiles.extend(student_mobile)
            elif self.filter_by == "classroom":
                student_course_ids = self.env["xe.classroom"].search(
                    [("id", "in", self.classroom_ids.ids)]
                )
                student_details = self.env["xe.student"].search(
                    [("classroom_id", "in", student_course_ids.ids)]
                )
                parent_mobiles = student_details.parent_ids.mapped("mobile")
                if parent_mobiles:
                    emp_mobiles.extend(parent_mobiles)
                student_mobile = student_details.mapped("mobile")
                if student_mobile:
                    emp_mobiles.extend(student_mobile)

            if emp_mobiles:
                emp_mobiles = list(filter(bool, emp_mobiles))
                if gateway_model.is_mtech_sms:
                    gateway_model.mtech_send_sms(
                        emp_mobiles, self.template_body, False, False, False
                    )
                else:
                    gateway_model.send_sms(emp_mobiles, self.template_body)
        else:
            raise UserError(_("Gateway not defined in SMS Template"))
