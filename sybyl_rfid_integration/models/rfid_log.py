# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api


class RFIDLogs(models.Model):
    _name = 'rfid.logs'
    _description = "RFID Logs"

    device_serial_number = fields.Char(string="Device Serial Number")
    badge_number = fields.Char(string="Badge Number")
    card_number = fields.Char(string="Card Number")
    name = fields.Char(string="Name")
    date = fields.Datetime(string="DateTime")