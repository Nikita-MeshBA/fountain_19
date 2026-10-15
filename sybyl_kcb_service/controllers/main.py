# pylint: disable=E0401
import json
import logging
from datetime import datetime

from odoo.http import request, JsonRPCDispatcher, Response
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, date_utils

from odoo import http

_logger = logging.getLogger(__name__)


def _response(self, result=None, error=None):
    response = {"jsonrpc": "2.0", "id": self.jsonrequest.get("id")}
    if error is not None:
        response["error"] = error
    if result is not None:
        response["result"] = result
    mime = "application/json"
    # body = json.dumps(response, default=date_utils.json_default)
    body = json.dumps(response, default=str)
    if request.env.context.get("kcb_service"):
        dtb_response = {}
        if error is not None:
            dtb_response = error
        if result is not None:
            dtb_response = result
        body = json.dumps(dtb_response)
    return Response(
        body,
        status=error and error.pop("http_status", 200) or 200,
        headers=[("Content-Type", mime), ("Content-Length", len(body))],
    )


setattr(JsonRPCDispatcher, "_response", _response)


class KCBBankServices(http.Controller):
    @http.route(
        "/verify/invoice/BillValidation", type="json", auth="public", csrf=False
    )
    def get_invoice_bill_validation(self, **kwargs):
        data = json.loads(request.httprequest.data)
        # data = kwargs
        # data = request.dispatcher.jsonrequest
        message = {
            "auth-fail": "AUTHENTICATION FAILED",
            "not-stu": "NOT A STUDENT",
        }
        db_list = http.db_list()
        if not db_list:
            return message["auth-fail"]
        db = db_list[0]
        data_key = ["requestId", "customerReference"]
        for dk in data_key:
            if dk not in data.keys():
                _logger.warning("**** Missing Key for " + str(dk))
            else:
                if data[dk] is None:
                    _logger.warning("**** Missing Value for " + str(dk))

        request_id = data.get("requestId")
        bill_ref_no = str(data.get("customerReference"))
        response_header = {}

        move_id = (
            request.env["account.move"].sudo().search([("name", "=", bill_ref_no)])
        )
        if move_id:
            if move_id.payment_state == "partial":
                bill_type = "PARTIAL"
            elif move_id.payment_state == "paid":
                bill_type = "FIXED"
            else:
                bill_type = move_id.payment_state
            request.update_context(kcb_service=True)
            response_header["billType"] = "PARTIAL"
            response_header["transactionID"] = request_id
            response_header["statusMessage"] = "Success"
            response_header["statusCode"] = 0
            response_header["CustomerName"] = (
                move_id.partner_id.name if move_id.partner_id else ""
            )
            response_header["billAmount"] = move_id.amount_residual
            response_header["currency"] = (
                move_id.currency_id.name if move_id.currency_id else ""
            )
            response_header["creditAccountIdentifier"] = ""
        else:
            request.update_context(kcb_service=True)
            response_header["transactionID"] = request_id
            response_header["statusCode"] = 1
            response_header["statusMessage"] = "Validation Failed"
            response_header["CustomerName"] = ""
            response_header["billAmount"] = ""
            response_header["currency"] = ""
            response_header["billType"] = ""
            response_header["creditAccountIdentifier"] = ""

        # move_rec = request.env['kcb.transaction'].sudo().search([('move_id', '=', move.id)])
        # kcb_transaction_rec = (
        #     request.env["kcb.transaction"]
        #     .sudo()
        #     .search(
        #         [("bill_ref_no", "=", bill_ref_no), ("request_id", "=", request_id)],
        #         limit=1,
        #     )
        # )
        # _logger.info("******" + str(kcb_transaction_rec))
        # response_header = {}
        # if kcb_transaction_rec:
        #     move_rec = kcb_transaction_rec.move_id
        #     if kcb_transaction_rec.move_id.payment_state == "partial":
        #         bill_type = "PARTIAL"
        #     elif kcb_transaction_rec.move_id.payment_state == "paid":
        #         bill_type = "FIXED"
        #     else:
        #         bill_type = kcb_transaction_rec.move_id.payment_state

        #     bill_amount = kcb_transaction_rec.dblAmount
        #     if kcb_transaction_rec.payment_ids:
        #         for payment in kcb_transaction_rec.payment_ids:
        #             if payment.amount != kcb_transaction_rec.dblAmount:
        #                 bill_type = "PARTIAL"
        #                 bill_amount = payment.amount
        #             else:
        #                 bill_type = "FIXED"
        #                 bill_amount = payment.amount
        #     request.update_context(kcb_service=True)
        #     # move_rec.creditAccountIdentifier if move_rec else ''
        #     response_header["transactionID"] = (
        #         move_rec.name if move_rec.name else kcb_transaction_rec.strTransNo
        #     )
        #     response_header["statusCode"] = 0
        #     response_header["statusMessage"] = "Success"
        #     response_header["customerName"] = (
        #         move_rec.partner_id.name
        #         if move_rec.partner_id
        #         else kcb_transaction_rec.firstName
        #     )
        #     response_header["billAmount"] = bill_amount
        #     response_header["currency"] = (
        #         move_rec.currency_id.name
        #         if move_rec.currency_id
        #         else kcb_transaction_rec.currency
        #     )
        #     response_header["billType"] = bill_type
        #     response_header[
        #         "creditAccountIdentifier"
        #     ] = kcb_transaction_rec.creditAccountIdentifier
        # else:
        #     request.update_context(kcb_service=True)
        #     response_header["statusCode"] = 1
        #     response_header["statusMessage"] = "Not Found"
        #     response_header["customerName"] = ""

        return response_header

    @http.route(
        "/processTransaction/BillNotification", type="json", auth="public", csrf=False
    )
    def process_bill_notification(self, **kwargs):
        data = json.loads(request.httprequest.data)
        # data_key = ["transactionReference", "requestId", "timestamp", "transactionAmount", "currency", "customerReference"
        #             "customerName", "customerMobileNumber", "balance", "narration", "creditAccountIdentifier", "middleName",
        #             "lastName"]
        # data = kwargs
        message = {
            "auth-fail": "AUTHENTICATION FAILED",
            "not-stu": "NOT A STUDENT",
        }
        db_list = http.db_list()
        if not db_list:
            return message["auth-fail"]
        db = db_list[0]
        data_key = [
            "transactionReference",
            "requestId",
            "timestamp",
            "transactionAmount",
            "currency",
            "customerReference" "customerName",
            "customerMobileNumber",
            "balance",
        ]
        for dk in data_key:
            # if data[dk] is None:
            if dk not in data.keys():
                _logger.warning("**** Missing key for " + str(dk))
            else:
                if data[dk] is None:
                    _logger.warning("**** Missing Value for " + str(dk))

        vals = {
            "strTransNo": data.get("transactionReference"),
            "request_id": data.get("requestId"),
            "dtTransDate": data.get("timestamp")
            and datetime.strptime(data.get("timestamp")[:-6], "%Y%m%d").strftime(
                DEFAULT_SERVER_DATE_FORMAT
            ),
            "dblAmount": data.get("transactionAmount"),
            "currency": data.get("currency"),
            "bill_ref_no": data.get("customerReference"),
            "firstName": data.get("customerName"),
            "mobile": data.get("customerMobileNumber"),
            "balance": data.get("balance"),
            "narration": data.get("narration"),
            # "transactionType": data.get("transactionType"),
            "creditAccountIdentifier": data.get("creditAccountIdentifier"),
            "middleName": data.get("middleName") if data.get("middleName") else "",
            "lastName": data.get("lastName") if data.get("lastName") else "",
            # "channelCode": data.get("channelCode"),
        }
        response_payload = {}
        transaction = (
            request.env["kcb.transaction"]
            .sudo()
            .search([("strTransNo", "=", data.get("transactionReference"))])
            # .search([("bill_ref_no", "=", data.get("customerReference"))])
        )
        if transaction:
            request.update_context(kcb_service=True)
            response_payload["statusCode"] = 1
            response_payload["statusMessage"] = "Duplicate Record"
            response_payload["transactionID"] = data.get("requestId")
        else:
            transaction = request.env["kcb.transaction"].sudo().create(vals)
            request.update_context(kcb_service=True)
            response_payload["statusCode"] = 0
            response_payload["statusMessage"] = "Notification received"
            response_payload["transactionID"] = data.get("requestId")

        return response_payload

    @http.route(
        "/processTransaction/BillNotificationNotSent",
        type="json",
        auth="public",
        csrf=False,
    )
    def process_bill_notification_not_sent(self, **kwargs):
        # data = json.loads(request.httprequest.data)
        data = kwargs
        message = {
            "auth-fail": "AUTHENTICATION FAILED",
            "not-stu": "NOT A STUDENT",
        }
        db_list = http.db_list()
        if not db_list:
            return message["auth-fail"]
        db = db_list[0]
        data_key = [
            "customerReference",
        ]
        for dk in data_key:
            # if data[dk] is None:
            if dk not in data.keys():
                _logger.warning("**** Missing Key for " + str(dk))
            else:
                if data[dk] is None:
                    _logger.warning("**** Missing Value for " + str(dk))
        bill_ref_no = str(data.get("customerReference"))
        kcb_transaction_rec = (
            request.env["kcb.transaction"]
            .sudo()
            .search(
                [("bill_ref_no", "=", bill_ref_no)],
                limit=1,
            )
        )
        response_header = {}
        if kcb_transaction_rec:
            request_id = kcb_transaction_rec.request_id
            move_rec = kcb_transaction_rec.move_id
            if kcb_transaction_rec.move_id.payment_state == "partial":
                bill_type = "PARTIAL"
            elif kcb_transaction_rec.move_id.payment_state == "paid":
                bill_type = "FIXED"
            else:
                bill_type = kcb_transaction_rec.move_id.payment_state

            bill_amount = kcb_transaction_rec.dblAmount
            if kcb_transaction_rec.payment_ids:
                for payment in kcb_transaction_rec.payment_ids:
                    if payment.amount != kcb_transaction_rec.dblAmount:
                        bill_type = "PARTIAL"
                        bill_amount = payment.amount
                    else:
                        bill_type = "FIXED"
                        bill_amount = payment.amount
            request.update_context(kcb_service=True)
            response_header["transactionID"] = kcb_transaction_rec.strTransNo
            response_header["requestId"] = request_id
            # "channelCode": data.get("channelCode"),
            response_header["timestamp"] = kcb_transaction_rec.dtTransDate
            response_header["currency"] = kcb_transaction_rec.currency
            response_header["customerReference"] = kcb_transaction_rec.bill_ref_no
            response_header["customerMobileNumber"] = kcb_transaction_rec.mobile
            # response_header["narration"] = kcb_transaction_rec.mobile
            # response_header["organizationShortCode"] = kcb_transaction_rec.mobile
            # response_header["tillNumber"] = kcb_transaction_rec.mobile
            response_header["statusCode"] = 0
            response_header["statusMessage"] = "Success"
            response_header["customerName"] = (
                move_rec.partner_id.name
                if move_rec.partner_id
                else kcb_transaction_rec.firstName
            )
            # response_header["billAmount"] = bill_amount
            response_header["amount"] = bill_amount
            response_header["currency"] = (
                move_rec.currency_id.name
                if move_rec.currency_id
                else kcb_transaction_rec.currency
            )
            response_header["billType"] = "PARTIAL"
            response_header[
                "creditAccountIdentifier"
            ] = kcb_transaction_rec.creditAccountIdentifier
        else:
            request.update_context(kcb_service=True)
            response_header["statusCode"] = 1
            response_header["statusMessage"] = "Not Found"
            response_header["customerName"] = ""

        return response_header
