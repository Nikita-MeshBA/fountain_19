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

    is_better_sms = fields.Boolean(default=False)
    sender_id = fields.Char()
    better_username = fields.Char()
    better_password = fields.Char()
    better_sms_type = fields.Selection([('trans', 'Trans'), ('promo', 'Promo')])
    better_coding = fields.Selection([('1', '1'), ('2', '2')], default='1', help="1 - English & 2 - Non-English")

    @api.onchange("is_better_sms")
    def _onchange_is_better_sms(self):
        if self.is_better_sms:
            self.url = "https://kenyasms.rpdigitalphone.com/smsnew/"
        if not self.is_better_sms:
            self.url = ""

    def create_url(self, message=None, number=None):
        better_sms_id = self.search([('is_better_sms', '=', True)], limit=1)
        sender_id = better_sms_id.sender_id
        username = better_sms_id.better_username
        password = better_sms_id.better_password
        sms_type = better_sms_id.better_sms_type
        coding = better_sms_id.better_coding

        request_url =  "%sHTTP/?username=%s&password=%s&thread_text=%s&thread_recievers=%s&sender=%s&coding=%s&sms_type=%s" % (better_sms_id.url, username, password, message, number, sender_id, coding, sms_type)
        return request_url

    def test_send_sms_connection(self):
        if self.is_better_sms:
            self.better_test_send_sms_connection()
        else:
            super(SmsGatewayConfigInherit, self).test_send_sms_connection()

    def better_test_send_sms_connection(self):
        message = "SMS Connection Established."
        request_url = self.create_url(message, self.phone_no)
        try:
            response = requests.post(url=request_url)
        except Exception as exception:
            raise UserError(
                _("Connection Test Failed! Here is what we got instead:\n %s")
                % ustr(exception)
            )
        if response.status_code == 200:
            _logger.warn(response.text)
            return True
        raise UserError(
            _("Connection Test Failed! Here is what we got instead:\n %s")
            % ustr(response.text)
        )

    def better_send_sms(self, message, numbers):
        res = {}
        try:
            for number in numbers:
                request_url = self.create_url(message, number)
                response = requests.post(url=request_url)
                result = {
                    "to_number": number,
                    "template_body": message,
                    "sms_gateway_id": self.id,
                    "response_status": response.status_code,
                    "response_content": response.text,
                    "company_id": self.env.company.id,
                }
                if response.status_code == 200:
                    result["state"] = "send"
                else:
                    result["state"] = "failed"
                    _logger.warn("Failed to send SMS", exc_info=True)
                self.env["bulk.sms.send.log"].create(result)
        except:
            _logger.warn("Failed to send SMS", exc_info=True)

    # def better_test_send_sms_connection(self):
    #     username = self.better_username
    #     password = self.better_password
    #     # Get Authentication Token
    #     values = {"email": email, "api_password": password}

    #     try:
    #         auth_response = requests.post(
    #             url=auth_url, headers=header, data=json.dumps(values)
    #         )
    #     except Exception as exception:
    #         raise UserError(
    #             _("Connection Test Failed! Here is what we got instead:\n %s")
    #             % ustr(exception)
    #         )
    #     auth_res = auth_response.json()

    #     if auth_res.get("status", False) == 0:
    #         self.auth_token = auth_res["token"]

    #         # Connection Success Message
    #         try:
    #             response = self.better_sms(
    #                 body="Successfully SMS Gateway Connected - %s" % (self.name),
    #                 to_number=self.phone_no,
    #                 record_id=False,
    #                 email=self.better_email,
    #                 api_password=self.better_api_password,
    #             )
    #         except Exception as exception:
    #             raise UserError(
    #                 _("Connection Test Failed! Here is what we got instead:\n %s")
    #                 % ustr(exception)
    #             )
    #         res = response.json()

    #         if not res.get("our_ref", False):
    #             err_message = res
    #             error_str = "Status Message:- " + str(err_message)
    #             raise UserError(
    #                 _("Connection Test Failed! Here is what we got instead:\n %s")
    #                 % ustr(error_str)
    #             )

    #         if res.get("balance"):
    #             self.better_balance = res.get("balance")
    #     else:
    #         raise UserError(_(str(auth_res)))

    # def better_send_sms(self, to_number, body, model, record_id, template_id):
    #     res = {}
    #     try:
    #         for num in to_number:
    #             if num:
    #                 response = self.better_sms(
    #                     body=body,
    #                     to_number=num,
    #                     record_id=record_id,
    #                     email=self.better_email,
    #                     api_password=self.better_api_password,
    #                 )
    #                 res = response.json()
    #                 if res.get("our_ref"):
    #                     result = {
    #                         "to_number": num,
    #                         "template_body": body,
    #                         "sms_gateway_id": self.id,
    #                         "response_status": res.get("message"),
    #                         "response_content": res,
    #                         "state": "send",
    #                         "company_id": self.env.company.id,
    #                     }
    #                     self.env["bulk.sms.send.log"].create(result)
    #                 else:
    #                     result = {
    #                         "to_number": num,
    #                         "template_body": body,
    #                         "sms_gateway_id": self.id,
    #                         "response_status": res.get("message"),
    #                         "response_content": res,
    #                         "state": "failed",
    #                         "company_id": self.env.company.id,
    #                     }
    #                     res = self.env["bulk.sms.send.log"].create(result)
    #                     _logger.warn("Failed to send SMS", exc_info=True)

    #                 if res.get("balance"):
    #                     self.better_balance = res.get("balance")
    #     except:
    #         _logger.warn("Failed to send SMS", exc_info=True)

    # def better_sms(self, body, to_number, record_id, email, api_password):
    #     auth_url = self.auth_url
    #     auth_token = self.auth_token
    #     # Get Authentication Token
    #     values = {"email": email, "api_password": api_password}
    #     try:
    #         auth_response = requests.post(
    #             url=auth_url, headers=header, data=json.dumps(values)
    #         )
    #         auth_res = auth_response.json()
    #         if auth_res.get("status") == 0:
    #             auth_token = auth_res["token"]
    #         else:
    #             return auth_response
    #     except Exception as exception:
    #         response = exception

    #     uid = uuid.uuid4()
    #     message_id = uid.hex
    #     values = {
    #         "token": auth_token,
    #         "phone_number": to_number,
    #         "unique_identifier": message_id,
    #         "sender_name": self.sender_id,
    #         "message": body,
    #     }
    #     response = requests.post(url=self.url, headers=header, data=json.dumps(values))
    #     return response


class SmsTemplateInherit(models.TransientModel):
    _inherit = "send.sms.template.new"

    def send_sms_new(self):
        gateway_model_id = self.sms_account_gateway_id
        if gateway_model_id:
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
                if gateway_model_id.is_better_sms:
                    gateway_model_id.better_send_sms(
                        self.template_body, emp_mobiles
                    )
                else:
                    gateway_model_id.send_sms(emp_mobiles, self.template_body)
        else:
            raise UserError(_("Gateway not defined in SMS Template"))
