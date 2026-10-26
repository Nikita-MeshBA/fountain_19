# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api


class RFIDDeviceConfiguration(models.Model):
    _name = 'rfid.device.configuration'
    _description = "RFID Device Configuration"
    _rec_name = 'device_name'

    device_name = fields.Char(string="Name",required=True)
    device_serial_number = fields.Char(string="Device Serial Number",required=True)