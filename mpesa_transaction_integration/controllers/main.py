# -*- coding: utf-8 -*-
# pylint: disable=E0401,C0114,C0115,C0116

import datetime
import json
import logging

from odoo.api import Environment
from odoo.http import request
from werkzeug.exceptions import BadRequest

import odoo
from odoo import fields, http, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class MpesaCashPayment(http.Controller):
    @http.route(
        "/v2/payment_notification",
        type="json",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def sapamacash_notification_json_get(self, **kwargs):
        _logger.info("data: transaction %s", str(json.loads(request.httprequest.data)))
        vals = {}
        post = json.loads(request.httprequest.data)
        if not post:
            _logger.info("Data is not getting!")
            result = {"ResultCode": 1, "ResultDesc": "Not Accepted"}
            return json.dumps(result)
        vals.update(
            {
                "name": post.get("FirstName"),
                "ref": post.get("BusinessShortCode"),
                "datas": json.dumps(post),
                "transaction_type": post.get("TransactionType"),
                "trans_id": post.get("TransID"),
                "trans_time": post.get("TransTime"),
                "trans_amount": float(post.get("TransAmount", 0.00)),
                "business_shortcode": post.get("BusinessShortCode"),
                "bill_ref_number": post.get("BillRefNumber"),
                "invoice_number": post.get("InvoiceNumber"),
                "org_account_balance": post.get("OrgAccountBalance"),
                "third_party_transid": post.get("ThirdPartyTransID"),
                "msisdn": post.get("MSISDN"),
                "first_name": post.get("FirstName"),
                "middle_name": post.get("MiddleName"),
                "last_name": post.get("LastName"),
            }
        )
        date = fields.Date.to_string(datetime.date.today())
        vals.update({"date": date})
        dbname = post.get("db", "")
        if not dbname:
            _logger.warning("Database name is not found!")
            result = {"ResultCode": 1, "ResultDesc": "Not Accepted"}
            return json.dumps(result)
        registry = odoo.registry(str(dbname))
        with registry.cursor() as cursor:
            try:
                env = Environment(cursor, SUPERUSER_ID, {})
                env["mpesa.payment.transaction"].sudo().create(vals)
                cursor.commit()
            except AttributeError:
                _logger.warning(
                    f"auth_signup not installed on database %s: oauth sign up cancelled.{dbname}"
                )
            except odoo.exceptions.AccessDenied:
                _logger.warning("AccessDenied")
            except Exception as error:
                if not str(error).isnumeric():
                    return json.dumps({"ResultCode": 1, "ResultDesc": "Not Accepted"})
        result = {"ResultCode": 0, "ResultDesc": "Accepted"}
        return json.dumps(result)

    @http.route(
        "/v1/payment_notification",
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def mpesa_notification_json_post(self, **kwargs):
        _logger.info(f"data: transaction {str(json.loads(request.httprequest.data))}")
        vals = {}
        post = json.loads(request.httprequest.data)
        if not post:
            _logger.info("Data is not getting!")
            result = {"ResultCode": 1, "ResultDesc": "Not Accepted"}
            return json.dumps(result)
        if post.get("company_name"):
            company = request.env["res.company"].sudo().search(
                [("name", "=", post.get("company_name"))]
            )
            if not company:
                _logger.info("Company is not available!")
                result = {"ResultCode": 1, "ResultDesc": "Not Accepted"}
                return json.dumps(result)
            vals.update({"company_id": company.id})

        vals.update(
            {
                "name": post.get("FirstName"),
                "ref": post.get("BusinessShortCode"),
                "datas": json.dumps(post),
                "transaction_type": post.get("TransactionType"),
                "trans_id": post.get("TransID"),
                "trans_time": post.get("TransTime"),
                "trans_amount": float(post.get("TransAmount", 0.00)),
                "business_shortcode": post.get("BusinessShortCode"),
                "bill_ref_number": post.get("BillRefNumber"),
                "invoice_number": post.get("InvoiceNumber"),
                "org_account_balance": post.get("OrgAccountBalance"),
                "third_party_transid": post.get("ThirdPartyTransID"),
                "msisdn": post.get("MSISDN"),
                "first_name": post.get("FirstName"),
                "middle_name": post.get("MiddleName"),
                "last_name": post.get("LastName"),
            }
        )
        date = fields.Date.to_string(datetime.date.today())
        vals.update({"date": date})
        dbname = post.get("db", "")
        # print('***********************************')
        # print(vals)
        # print('************************************')
        # dbname = 'xenesis_test'
        _logger.info(vals)
        if not dbname:
            _logger.warning("Database name is not found!")
            result = {"ResultCode": 1, "ResultDesc": "Not Accepted"}
            return json.dumps(result)
        registry = odoo.registry(str(dbname))
        with registry.cursor() as cursor:
            try:
                env = Environment(cursor, SUPERUSER_ID, {})
                env["mpesa.payment.transaction"].sudo().create(vals)
                cursor.commit()
            except AttributeError:
                _logger.warning(
                    f"auth_signup not installed on database %s: oauth sign up cancelled. {dbname}"
                )
            except odoo.exceptions.AccessDenied:
                _logger.warning("AccessDenied!!")
            except Exception as error:
                if not str(error).isnumeric():
                    return json.dumps({"ResultCode": 1, "ResultDesc": "Not Accepted"})
        result = {"ResultCode": 0, "ResultDesc": "Accepted"}
        return json.dumps(result)

    @http.route(
        "/payment_notification",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def mpesa_notification(self, dbname="", **post):
        _logger.info("data: transaction %s", str(post))
        vals = {}
        if not post:
            _logger.info("Data is not getting!")
            return ""
        vals.update(
            {
                "name": post.get("FirstName"),
                "ref": post.get("BusinessShortCode"),
                "data": json.dumps(post),
                "transaction_type": post.get("TransactionType"),
                "trans_id": post.get("TransID"),
                "trans_time": post.get("TransTime"),
                "trans_amount": float(post.get("TransAmount", 0.00)),
                "business_shortcode": post.get("BusinessShortCode"),
                "invoice_number": post.get("BillRefNumber"),
                "bill_ref_number": post.get("BillRefNumber"),
                "org_account_balance": post.get("OrgAccountBalance"),
                "third_party_transid": post.get("ThirdPartyTransID"),
                "msisdn": post.get("MSISDN"),
                "first_name": post.get("FirstName"),
                "middle_name": post.get("MiddleName"),
                "last_name": post.get("LastName"),
            }
        )
        if post.get("date"):
            date = datetime.datetime.strptime(post["date"], "%Y-%m-%d").date()
            vals.update({"date": date})
        if not dbname:
            _logger.warning("Database name is not found!")
            return ""
        registry = odoo.registry(str(dbname))
        error_message = False
        with registry.cursor() as cursor:
            try:
                env = Environment(cursor, SUPERUSER_ID, {})
                env["mpesa.payment.transaction"].sudo().create(vals)
                cursor.commit()
            except AttributeError:
                # auth_signup is not installed
                _logger.warning(
                    f"auth_signup not installed on database %s: oauth sign up cancelled. {dbname}"
                )
            except Exception as error:
                error_message = (
                    "mpesa payment transaction is not created due to user auth"
                )
                _logger.warning(error_message)
        if error_message:
            raise BadRequest(error_message)
        return ""
