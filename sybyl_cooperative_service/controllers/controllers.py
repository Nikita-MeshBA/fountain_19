import logging

from dateutil import parser
from odoo.exceptions import AccessError, AccessDenied
import json
from odoo import fields, http, _
from odoo.http import request
_logger = logging.getLogger(__name__)


class SybylCooperativeService(http.Controller):

    def get_json_context(self):
        context = dict(request.env.context)
        context.update({
            "remove_jsonrpc": True,
        })
        request.env.context = context

    def failure_response(self):
        response_dict = {
            "responseCode":"401",
            "responseDescription":"The caller is not authorized for this request"
        }
        return response_dict

    def check_user(self, uid=None):
        if uid is None:
            uid = request.uid
        is_system = request.env['res.users'].browse(uid)._is_system()
        if not is_system:
            return self.failure_response()
        else:
            return self.check_request_call()

    def _authenticate_user(self, db, username, password):
        try:
            authenticate_response_uid = http.request.session.authenticate(
                db, username, password
            )
            return self.check_user(authenticate_response_uid)
        except AccessError as exc:
            return self.failure_response()
        except AccessDenied as ade:
            return self.failure_response()
        print("authenticate_response",authenticate_response_uid)

    def check_request_call(self):
        if http.request.httprequest.method == 'POST':
            return None
        else:
            return {
            "responseCode":"404",
            "responseDescription":"The task/operation does not exist"
        }

    @http.route("/validate/account", auth="public", type="json")
    def validate_account(self):
        try:
            required_header_params = ['serviceName', 'messageID', 'connectionID', 'connectionPassword']
            required_request_params = ['TransactionReferenceCode', 'TransactionDate', 'InstitutionCode']
            request_json = json.loads(request.httprequest.data)

            for param in required_header_params:
                if param not in request_json['header'] or not request_json['header'][param]:
                    self.get_json_context()
                    return {"responsecode": "400", "responseDescription": "parameters passed are not valid or they are missing."}
            
            for param in required_request_params:
                if param not in request_json['request'] or not request_json['request'][param]:
                    self.get_json_context()
                    return {"responsecode": "400", "responseDescription": "parameters passed are not valid or they are missing."}
            
            response = self._authenticate_user(
                http.request.db,
                username=request_json.get("header", {}).get("connectionID"),
                password=request_json.get("header", {}).get(
                    "connectionPassword"
                ),
            )
            if response:
                self.get_json_context()
                return response
            student_id, invoice_id = self._find_student_or_invoice(request_json)
            status_code = 200
            if student_id:
                status_description = "Successfully validated student"
            elif invoice_id:
                status_description = "Successfully validated Invoice"
            else:
                status_code, status_description = 204, "Student/Invoice not found in system"
            response = self._prepare_validate_response(
                request_json,
                status_code,
                status_description,
                student_id,
                invoice_id,
            )
            log_id = self._log_transaction(
                "/validate/account",
                request_json,
                response,
                student_id,
                invoice_id,
            )
            self.get_json_context()
            return response
        except Exception as e:
            self.get_json_context()
            return {
                "responseCode":"405",
                "responseDescription":"A serious problem has occurred."
            }



    def _find_student_or_invoice(self, json_request):
        student_id = (
            http.request.env["xe.student"]
            .sudo()
            .search(
                [
                    (
                        "roll_number",
                        "=",
                        json_request.get("request").get("TransactionReferenceCode"),
                    )
                ],
                limit=1,
            )
        )
        invoice_id = False
        if not student_id:
            invoice_id = (
                http.request.env["account.move"]
                .sudo()
                .search(
                    [
                        (
                            "name",
                            "=",
                            json_request.get("request").get("TransactionReferenceCode"),
                        )
                    ],
                    limit=1,
                )
            )
            if invoice_id:
                _logger.info("\n Found in invoices : %s ", invoice_id)
        else:
            _logger.info("Found in students : %s ", student_id)
        return student_id, invoice_id

    def _prepare_validate_response(
        self, json_request, status_code, status_description, student_id, invoice_id
    ):
        response_dict = {}
        if student_id:
            response_dict = {
                "TransactionReferenceCode": json_request.get("request", {}).get(
                    "TransactionReferenceCode"
                ),
                "TransactionDate": json_request.get("request", {}).get(
                    "TransactionDate"
                ),
                "TotalAmount": student_id.total_balance_partner,
                "Currency": student_id.currency_id.name,
                "AdditionalInfo": student_id.name,
                "AccountNumber": json_request.get("request", {}).get(
                    "TransactionReferenceCode"
                ),
                "AccountName": student_id.name,
                "InstitutionCode": json_request.get("request", {}).get(
                    "InstitutionCode"
                ),
                "InstitutionName": student_id.company_id.name,
            }
        if invoice_id:
            response_dict = {
                "TransactionReferenceCode": json_request.get("request", {}).get(
                    "TransactionReferenceCode"
                ),
                "TransactionDate": invoice_id.date,
                "TotalAmount": invoice_id.amount_residual_signed,
                "Currency": invoice_id.currency_id.name,
                "AdditionalInfo": invoice_id.partner_id.name,
                "AccountNumber": json_request.get("request", {}).get(
                    "TransactionReferenceCode"
                ),
                "AccountName": invoice_id.partner_id.name,
                "InstitutionCode": json_request.get("request", {}).get(
                    "InstitutionCode"
                ),
                "InstitutionName": invoice_id.company_id.name,
            }
        return {
            "header": {
                "messageID": json_request.get("header", {}).get("messageID"),
                "statusCode": status_code,
                "statusDescription": status_description,
            },
            "response": response_dict,
        }

    @http.route("/payment/advise/notification", auth="public", type="json")
    def payment_advise_notification(self, **kw):
        try:
            required_header_params = ['serviceName', 'messageID', 'connectionID', 'connectionPassword']
            required_request_params = [
                'TransactionReferenceCode', 'TransactionDate', 'TotalAmount', 'Currency', 'DocumentReferenceNumber',
                'BankCode', 'BranchCode', 'PaymentDate', 'PaymentReferenceCode', 'PaymentCode', 'PaymentMode',
                'PaymentAmount', 'AdditionalInfo', 'AccountNumber', 'AccountName', 'InstitutionCode', 'InstitutionName'
            ]
            request_json = json.loads(request.httprequest.data)
            
            for param in required_header_params:
                if param not in request_json['header'] or not request_json['header'][param]:
                    self.get_json_context()
                    return {"responsecode": "400", "responseDescription": "parameters passed are not valid or they are missing."}
            
            for param in required_request_params:
                if param not in request_json['request'] or not request_json['request'][param]:
                    self.get_json_context()
                    return {"responsecode": "400", "responseDescription": "parameters passed are not valid or they are missing."}
        
            response = self._authenticate_user(
                http.request.db,
                username=request_json.get("header", {}).get("connectionID"),
                password=request_json.get("header", {}).get(
                    "connectionPassword"
                ),
            )
            if response:
                self.get_json_context()
                return response
            coop_bank_transaction_id, status_code, status_description = (
                self._update_payment_advice_notification(request_json)
            )
            # status_code, status_description = (
            #     200,
            #     "Payment successfully received" if coop_bank_transaction_id else 402,
            #     "Duplicate transaction detected",
            # )
            response = self._prepare_response(
                coop_bank_transaction_id, status_code, status_description
            )
            log_id = self._log_transaction(
                "/payment/advise/notification",
                request_json,
                response,
                coop_bank_transaction_id=coop_bank_transaction_id,
            )
            self.get_json_context()
            return response
        except Exception as e:
            _logger.error(f"Error Occured while executing: {str(e)}")
            self.get_json_context()
            return {
                "responseCode":"405",
                "responseDescription":"A serious problem has occurred."
            }

    def _update_payment_advice_notification(self, json_request):
        status_code, status_description = 402, "Duplicate transaction detected"
        coop_bank_transaction_id = (
            http.request.env["coop.bank.transaction"]
            .sudo()
            .search(
                [("message_id", "=", json_request.get("header", {}).get("messageID"))],
                limit=1,
            )
        )
        if coop_bank_transaction_id:
            status_code = 204
            status_description = (
                "Duplicate transaction detected."
            )
        else:
            coop_bank_transaction_id = (
                http.request.env["coop.bank.transaction"]
                .sudo()
                .search(
                    [
                        (
                            "transaction_reference_code",
                            "=",
                            json_request.get("request", {}).get(
                                "TransactionReferenceCode"
                            ),
                        )
                    ],
                    limit=1,
                )
            )
            if coop_bank_transaction_id:
                status_code = 204
                status_description = "Duplicate transaction detected."
            else:
                coop_bank_transaction_id = self._create_transaction(json_request)
                # if not isinstance(coop_bank_transaction_id,dict):
                if coop_bank_transaction_id:
                    status_code = 200
                    status_description = "Success"
                # else:
                #     coop_bank_transaction_id = None
                #     status_code = 400
                #     status_description = "The parameters passed are not valid or they are missing:Student or Invoice not found"
        return coop_bank_transaction_id, status_code, status_description

    def _create_transaction(self, json_request):
        student_id, invoice_id = self._find_student_or_invoice(json.loads(request.httprequest.data))
        # if not student_id and not invoice_id:
        #     return {}
        transaction_data = {
            "name": json_request.get("header", {}).get("serviceName"),
            "message_id": json_request.get("header", {}).get("messageID"),
            "connection_id": json_request.get("header", {}).get("connectionID"),
            "transaction_reference_code": json_request.get("request", {}).get(
                "TransactionReferenceCode"
            ),
            "transaction_date": json_request.get("request", {}).get("TransactionDate"),
            "transaction_datetime": fields.Datetime.to_string(
                parser.parse(json_request.get("request", {}).get("TransactionDate"))
            ),
            "total_amount": json_request.get("request", {}).get("TotalAmount"),
            "currency": json_request.get("request", {}).get("Currency"),
            "document_reference_number": json_request.get("request", {}).get(
                "DocumentReferenceNumber"
            ),
            "bank_code": json_request.get("request", {}).get("BankCode"),
            "branch_code": json_request.get("request", {}).get("BranchCode"),
            "payment_date": json_request.get("request", {}).get("PaymentDate"),
            "payment_reference_code": json_request.get("request", {}).get(
                "PaymentReferenceCode"
            ),
            "payment_code": json_request.get("request", {}).get("PaymentCode"),
            "payment_mode": json_request.get("request", {}).get("PaymentMode"),
            "payment_amount": json_request.get("request", {}).get("PaymentAmount"),
            "additional_info": json_request.get("request", {}).get("AdditionalInfo"),
            "account_number": json_request.get("request", {}).get("AccountNumber"),
            "account_name": json_request.get("request", {}).get("AccountName"),
            "institution_code": json_request.get("request", {}).get("InstitutionCode"),
            "institution_name": json_request.get("request", {}).get("InstitutionName"),
            "student_id": student_id.id,
            "invoice_id": invoice_id.id if invoice_id else None,
        }
        return http.request.env["coop.bank.transaction"].sudo().create(transaction_data)

    def _process_transaction(self, coop_bank_transaction_id):
        response_dict = {}
        if coop_bank_transaction_id:
            if (
                coop_bank_transaction_id.student_id
                or coop_bank_transaction_id.invoice_id
            ):
                response_dict = {
                    "TotalAmount": (
                        coop_bank_transaction_id.student_id.total_balance_partner
                        if coop_bank_transaction_id.student_id
                        else coop_bank_transaction_id.total_amount
                    ),
                    "AdditionalInfo": (
                        coop_bank_transaction_id.student_id.name
                        if coop_bank_transaction_id.student_id
                        else coop_bank_transaction_id.additional_info
                    ),
                    "AccountNumber": coop_bank_transaction_id.account_number,
                    "AccountName": coop_bank_transaction_id.account_name,
                    "InstitutionCode": coop_bank_transaction_id.institution_code,
                    "InstitutionName": coop_bank_transaction_id.institution_name,
                }
        return response_dict

    def _prepare_response(
        self,
        coop_bank_transaction_id,
        status_code,
        status_description,
    ):
        response_dict = {}
        if coop_bank_transaction_id:
            response_dict = {
                "TransactionReferenceCode": coop_bank_transaction_id.transaction_reference_code,
                "TransactionDate": coop_bank_transaction_id.transaction_date,
                "TotalAmount": coop_bank_transaction_id.total_amount,
                "Currency": coop_bank_transaction_id.currency,
                "AdditionalInfo": coop_bank_transaction_id.additional_info,
                "AccountNumber": coop_bank_transaction_id.account_number,
                "AccountName": coop_bank_transaction_id.account_name,
                "InstitutionCode": coop_bank_transaction_id.institution_code,
                "InstitutionName": coop_bank_transaction_id.institution_name,
                "TransactionAmount": coop_bank_transaction_id.total_amount,
            }
        return {
            "header": {
                "messageID": (
                    coop_bank_transaction_id.message_id
                    if coop_bank_transaction_id
                    else None
                ),
                "statusCode": status_code,
                "statusDescription": status_description,
            },
            "response": response_dict,
        }

    def _log_transaction(
        self,
        url_endpoint,
        json_request,
        response,
        student_id=False,
        invoice_id=False,
        coop_bank_transaction_id=False,
    ):
        coop_bank_log_id = (
            http.request.env["coop.bank.log"]
            .sudo()
            .create(
                {
                    "name": json_request,
                    "url_endpoint": url_endpoint,
                    "response": response,
                    "coop_bank_transaction_id": (
                        coop_bank_transaction_id.id
                        if coop_bank_transaction_id
                        else None
                    ),
                }
            )
        )
        return coop_bank_log_id
