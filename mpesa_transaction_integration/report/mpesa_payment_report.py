# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import api, models


class MpesaTransactionReport(models.AbstractModel):
    _name = "report.mpesa_payment_transaction.report_transactiondetails"

    @api.model
    def _get_report_values(self, docids, data=None):
        transactions = self.env["mpesa.payment.transaction"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "mpesa.payment.transaction",
            "docs": transactions,
            "data": data,
        }
