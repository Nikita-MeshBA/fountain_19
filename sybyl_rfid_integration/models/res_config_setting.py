# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    databse_url = fields.Char(string="Databse Url", readonly=False,config_parameter='sybyl_rfid_integration.databse_url')
    databse_port = fields.Char(string="Databse Port", readonly=False,config_parameter='sybyl_rfid_integration.databse_port')
    authorization_value = fields.Char(string="Authorization Value", readonly=False,config_parameter='sybyl_rfid_integration.authorization_value')