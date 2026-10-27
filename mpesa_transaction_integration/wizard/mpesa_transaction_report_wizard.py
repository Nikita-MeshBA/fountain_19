# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# pylint: disable=E0401,C0114,C0115,C0116

from odoo import api, fields, models


class MpesaTransactionReportWizard(models.TransientModel):
    _name = "mpesa.transaction.report.wizard"
    _description = "Mpesa Transaction Wizard"

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    def get_report_datas(self):
        transactions = self.env["mpesa.payment.transaction"].search(
            [("date", ">=", self.start_date), ("date", "<=", self.end_date)]
        )
        transaction_details = []
        for trans in transactions:
            name = trans.first_name
            if trans.middle_name:
                name = name + " " + trans.middle_name
            if trans.last_name:
                name = name + " " + trans.last_name
            transaction_type = trans.transaction_type
            date = trans.date
            bill_ref_number = trans.bill_ref_number

            if bill_ref_number:
                bill_ref_number = bill_ref_number[:10]

            if transaction_type:
                transaction_type = transaction_type[:10]

            invoice_name = trans.invoice_name

            if invoice_name:
                invoice_name = invoice_name[:15]
            trans_amount = trans.trans_amount
            trans_dict = {
                "name": name,
                "transaction_type": transaction_type,
                "date": date,
                "bill_ref_number": bill_ref_number,
                "invoice_name": invoice_name,
                "trans_amount": trans_amount,
            }
            transaction_details.append(trans_dict)
        return transaction_details

    def print_xlsx(self):
        transaction_details = self.get_report_datas()
        filters = {"start_date": self.start_date, "end_date": self.end_date}
        data = {
            "transaction_data": transaction_details,
            "Filters": filters,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        return self.env.ref(
            "mpesa_transaction_integration.mpesa_transaction_xlsx_report"
        ).report_action(self, data=data)

    def print_pdf(self):
        transaction_details = self.get_report_datas()
        filters = {"start_date": self.start_date, "end_date": self.end_date}
        data = {
            "transaction_data": transaction_details,
            "Filters": filters,
            "start_date": self.start_date,
        }
        return (
            self.env.ref(
                "mpesa_transaction_integration.action_wizard_mpesa_transaction"
            )
            .with_context(landscape=False)
            .report_action(self, data=data)
        )

    def get_report(self):
        transaction_details = self.get_report_datas()
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "date_start": self.start_date,
                "date_end": self.end_date,
                "transaction_details": transaction_details,
            },
        }
        return (
            self.env.ref("mpesa_transaction_integration.mpesatrans_report")
            .with_context(landscape=False)
            .report_action(self, data=data)
        )

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     print ('___ data : ', data);
    #     print ('___ data.get("docids") : ', data.get("docids"));
    #     docs = self.env["xe.student"].browse(data.get("docids"))
    #     attribute_lines = self.env["xe.certificate.atts.lines"].browse(
    #         data.get("attribute_lines")
    #     )
    #     current_date = date.today().strftime("%d-%m-%Y")
    #     return {
    #         "doc_ids": docids,
    #         "doc_model": "xe.student",
    #         "docs": docs,
    #         "data": data,
    #         "current_date": current_date,
    #         "attribute_lines": attribute_lines,
    #     }


class ReportMpesatrans(models.AbstractModel):
    _name = "report.mpesa_transaction_integration.mpesatrans_report_view"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data["form"]["date_start"]
        date_end = data["form"]["date_end"]
        transaction_details = data["form"]["transaction_details"]
        docs = [{"name": "rit", "type": "1"}, {"name": "rits", "type": "2"}]
        return {
            "doc_ids": data["ids"],
            "doc_model": data["model"],
            "date_start": date_start,
            "date_end": date_end,
            "transaction_details": transaction_details,
            "docs": docs,
        }
