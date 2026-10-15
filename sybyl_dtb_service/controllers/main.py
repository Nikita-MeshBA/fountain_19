# pylint: disable=E0401,C0114,C0115,C0116
import json
from datetime import datetime

from odoo.http import request, JsonRPCDispatcher, Response
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, date_utils

from odoo import http


def _json_response(self, result=None, error=None):
    response = {"jsonrpc": "2.0", "id": self.jsonrequest.get("id")}
    dtb_response = {}
    if error is not None:
        response["error"] = error
    if result is not None:
        response["result"] = result
    mime = "application/json"
    body = json.dumps(response, default=date_utils.json_default)
    if self.env.context.get("dtb_service"):
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


setattr(JsonRPCDispatcher, "_json_response", _json_response)


class DTBBankServices(http.Controller):
    @http.route("/webhook-transaction", type="json", auth="public", csrf=False)
    def ProcessTransaction(self):
        data = json.loads(request.httprequest.data)
        notify_data = data
        response = {"xref": notify_data.get("xref")}
        try:
            vals = {}
            if notify_data.get("account_number"):
                vals["bill_ref_no"] = notify_data.get("account_number")
            if notify_data.get("xref"):
                vals["xref"] = notify_data.get("xref")
            if notify_data.get("cbs_reference"):
                vals["cbs_reference"] = notify_data.get("cbs_reference")
            if notify_data.get("cbs_module"):
                vals["cbs_module"] = notify_data.get("cbs_module")
            if notify_data.get("account_number"):
                vals["account_number"] = notify_data.get("account_number")
            if notify_data.get("branch_code"):
                vals["branch_code"] = notify_data.get("branch_code")
            if notify_data.get("currency"):
                vals["currency"] = notify_data.get("currency")
            if notify_data.get("transaction_time"):
                vals["dtTransDate"] = datetime.strptime(
                    notify_data["transaction_time"], "%Y%m%d %H:%M:%S"
                ).strftime(DEFAULT_SERVER_DATE_FORMAT)

            if notify_data.get("value_date"):
                vals["value_date"] = notify_data.get("value_date")
            if notify_data.get("amount"):
                vals["dblAmount"] = notify_data.get("amount")
            if notify_data.get("reversal_indicator"):
                vals["reversal_indicator"] = notify_data.get("reversal_indicator")

            if notify_data.get("debit_credit_indicator"):
                vals["debit_credit_indicator"] = notify_data.get(
                    "debit_credit_indicator"
                )

            if notify_data.get("exchange_rate"):
                vals["exchange_rate"] = notify_data.get("exchange_rate")

            if notify_data.get("financial_year"):
                vals["financial_year"] = notify_data.get("financial_year")

            if notify_data.get("transaction_code"):
                vals["transaction_code"] = notify_data.get("transaction_code")

            if notify_data.get("transaction_description"):
                vals["transaction_description"] = notify_data.get(
                    "transaction_description"
                )
            if notify_data.get("virtual_pan"):
                vals["virtual_pan"] = notify_data.get("virtual_pan")

            if notify_data.get("rrn"):
                vals["rrn"] = notify_data.get("rrn")
            if notify_data.get("customer_name"):
                vals["customer_name"] = notify_data.get("customer_name")
            if notify_data.get("customer_mobile"):
                vals["customer_mobile"] = notify_data.get("customer_mobile")

            if notify_data.get("serial_number"):
                vals["serial_number"] = notify_data.get("serial_number")
            if notify_data.get("narration"):
                vals["narration"] = notify_data.get("narration")
            if notify_data.get("transaction_time"):
                vals["transaction_time"] = notify_data.get("transaction_time")
            transaction_count = (
                request.env["dtb.transaction"]
                .sudo()
                .search_count([("xref", "=", notify_data.get("xref"))])
            )
            if transaction_count == 0:
                transaction = request.env["dtb.transaction"].sudo().create(vals)
                request.update_context(dtb_service=True)
                response["user_reference"] = transaction.name
                response["ack_code"] = "00"
                response["ack_description"] = "SUCCESS"
            else:
                response["user_reference"] = False
                response["ack_code"] = "409"
                response["ack_description"] = "Duplicate Record"

        except Exception as error:
            response["user_reference"] = False
            response["ack_code"] = "400"
            response["ack_description"] = "Invalid Payload"
        return response
