# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from datetime import datetime
import base64

class RFIDSessionConfiguration(models.Model):
    _name = 'rfid.session.configuration'
    _description = "RFID Session Configuration"

    session_id = fields.Char(string="Session ID",required=True, default=lambda x: _('New'),readonly=True)
    session_name = fields.Char(string="Name",required=True)
    device_id = fields.Many2one('rfid.device.configuration',string="Device Serial Number",required=True)
    current_session_state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        string='Session State',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='closed',
    )
    start_at = fields.Datetime(string='Opening Date', readonly=True)
    stop_at = fields.Datetime(string='Closing Date', readonly=True, copy=False)
    session_limit = fields.Integer(string="Session Limit")

    def fetch_latest_scan(self,session_id):
        # fetch_latest_request = self.env['rfid.request.record'].sudo().search([('session_id','=',int(session_id['session_id']),('session_state','=','open'))], order='create_date desc', limit=1)
        fetch_latest_request = self.env['rfid.request.record'].sudo().search([('session_id','=',int(session_id['session_id'])),('session_state','=','open'),('is_loaded','=',False)], order='create_date desc', limit=1)

        data = {}
        if fetch_latest_request:
            data.update({
            "student_name" : fetch_latest_request.student_id.name,
            "date": fetch_latest_request.create_date,
            "roll_number": fetch_latest_request.student_id.roll_number,
            "class": fetch_latest_request.student_id.course_id.name,
            "classroom" : fetch_latest_request.student_id.classroom_id.name,
            "image": fetch_latest_request.student_id.image_1920,
            "fee_balance":fetch_latest_request.student_id.total_balance_partner,
            "status": "approved" if fetch_latest_request.session_id.session_limit > fetch_latest_request.student_id.total_balance_partner else "declined"
            })
            fetch_latest_request.write({'is_loaded':True})
        if 'direct' in self.env.context:
            return fetch_latest_request

        return data
    
    @api.model
    def create(self, vals):
        """Create new Sequence"""
        if vals.get("name", "New") == "New":
            vals["session_id"] = self.env["ir.sequence"].next_by_code("rfid.sessionid.seq") or "New"
        result = super(RFIDSessionConfiguration, self).create(vals)
        return result

    def action_pos_config_modal_edit(self):
        return {
            'view_mode': 'form',
            'res_model': 'rfid.session.configuration',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def open_ui(self):
        self.ensure_one()
        if self.current_session_state == 'closed':
            self.start_at = datetime.now()
        if self.current_session_state != 'open':
            self.current_session_state = 'open'
        fetch_latest_student = self.env['rfid.request.record'].sudo().search([('session_id','=',self.id)], order='create_date desc', limit=1)
        return {
                'type': 'ir.actions.client',
                'tag': 'student_dialog',
                'params': {
                }
                }

    def open_existing_session_cb(self,session_id):
        """ close session button

        access session form to validate entries
        """
        session_id = self.browse(int(session_id['session_id']))
        session_id.stop_at = datetime.now()
        session_id.current_session_state = 'closed'
        latest_fetch = session_id.with_context(direct=True).fetch_latest_scan(session_id={'session_id':session_id.id})
        print ('___ latest_fetch : ', latest_fetch);
        latest_fetch.write({'session_state':'closed'})

class RFIDRequestedRecord(models.Model):
    _name = 'rfid.request.record'
    _description = "RFID Requested Record"

    session_id = fields.Many2one('rfid.session.configuration')
    student_id = fields.Many2one('xe.student')
    card_id = fields.Many2one('rfid.card.configuration')
    is_loaded = fields.Boolean("Loaded",default=False)
    
    session_state = fields.Selection(selection=[
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        string='state',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='open',)