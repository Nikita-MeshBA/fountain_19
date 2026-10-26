import logging

from dateutil import parser
from odoo.exceptions import AccessError, AccessDenied
import json
from odoo import fields, http, _
from odoo.http import request
_logger = logging.getLogger(__name__)

class SybylRFIDIntegration(http.Controller):

    @http.route("/rfid/export_service/notification", auth="public", type="json",methods=['POST'])
    def rfid_export_service_(self):
        try:
            data = request.dispatcher.jsonrequest
            required_params = ['deviceSerialNumber', 'badgeNumber', 'cardNumber', 'name',"date"]
            request_json = json.loads(request.httprequest.data)
            for key in required_params:
                if key not in request_json:
                    return {"responsecode": "400", "responseDescription": "parameters passed are not valid or they are missing."}
            vals = {
            'device_serial_number':request_json.get("deviceSerialNumber"),
            'badge_number':request_json.get("badgeNumber"),
            'card_number':request_json.get("cardNumber"),
            'name':request_json.get("name"),
            'date':request_json.get("date"),
            }
            device_id = request.env['rfid.device.configuration'].search([('device_serial_number','=',request_json.get("deviceSerialNumber"))])
            if device_id:
                session_id = request.env['rfid.session.configuration'].search([('device_id','=',device_id.id)])
                card_id = request.env['rfid.card.configuration'].search([('badge_number','=',request_json.get("badgeNumber"))])
                student_id = card_id.student_id if card_id else None
                if not session_id or not card_id:
                    return {
                        "responseCode":"400",
                        "result":"Failed",
                        "responseDescription":"Session or Card Not found."
                    }
                request_record = request.env['rfid.request.record'].create({
                    'session_id':session_id.id,
                    'student_id':student_id.id,
                    'card_id':card_id.id,
                    'is_loaded':False
                    })
                log_id =  http.request.env["rfid.logs"].create(vals)
                if request_record:
                    return {
                        "responseCode":"200",
                        "responseDescription":"Success."
                    }

            else:
                return {
                        "responseCode":"400",
                        "result":"Failed",
                        "responseDescription":"Device Not Found."
                    }
        except Exception as e:
            _logger.error(f"Error Occured while executing: {str(e)}")
            return {
                "responseCode":"400",
                "result":"Failed",
                "responseDescription":"Serious Problem Occured."
            }