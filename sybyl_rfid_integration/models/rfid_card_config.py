# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import base64
import requests
import json


class RFIDCardConfiguration(models.Model):
    _name = 'rfid.card.configuration'
    _description = "RFID Card Configuration"
    _rec_name = 'card_number'

    badge_number = fields.Char(string="Badge Number",required=True)
    student_id = fields.Many2one('xe.student',string="Name",required=True)
    card_number = fields.Char(string="Card Number",required=True)
    device_id = fields.Many2one('rfid.device.configuration',string="Device",required=True)
    image_data = fields.Image(related='student_id.image_1920')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('add_to_db', 'Added To Database'),
            ('add_to_device', 'Added To Device'),
        ],
        string='state',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )

    _sql_constraints = [
        ('badge_number_uniq', 'unique (badge_number)', "BadgeNumber already exists!"),
    ]
        
    def check_rfid_configuration(self):
        
        databse_url = self.env['ir.config_parameter'].sudo().get_param('sybyl_rfid_integration.databse_url')
        databse_port = self.env['ir.config_parameter'].sudo().get_param('sybyl_rfid_integration.databse_port')
        authorization_value = self.env['ir.config_parameter'].sudo().get_param('sybyl_rfid_integration.authorization_value')
        if not databse_url or not databse_port or not authorization_value:
            raise UserError(_("Please cofigure Missing value for RFID Configuration"))
        return databse_url,databse_port,authorization_value

    def create_update_to_database(self):
        databse_url,databse_port,authorization_value = self.check_rfid_configuration()
        api_url = databse_url+":"+databse_port+"/api_saveemployee"
        pass
        headers={
            "Content-Type": "application/json",
            "token":authorization_value
        }
        data= self.image_data.decode('utf-8')
        params = {
        "BadgeNumber":self.badge_number,
        "Name": self.student_id.name,
        "CardNo": self.card_number,
        "template": data
,
        }
        post_response = requests.post(api_url, json=params, headers=headers)

        response_data = json.loads(post_response.content.decode("utf-8"))
        if response_data['result'] == 'Success':
            self.state = 'add_to_db'

    def add_to_device(self):
        databse_url,databse_port,authorization_value = self.check_rfid_configuration()
        api_url = databse_url+":"+databse_port+"/api_saveemployee"

        headers={
            "Content-Type": "application/json",
            "token":authorization_value
        }
        params = {
        "BadgeNumber":self.badge_number,
        "DeviceSerialNumber":self.device_id.device_serial_number
        }
        post_response = requests.post(api_url, json=params, headers=headers)

        response_data = json.loads(post_response.content.decode("utf-8"))
        if response_data['result'] == 'Success':
            self.state = 'add_to_device'
