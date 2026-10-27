from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT,
)
from datetime import date


class ReportBankStatement(models.AbstractModel):
    _name = "report.bi_bank_statement_reconciliation.bankstatment_view"
    _description = "Bank Statement Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        today = str(date.today())
        today = datetime.strftime(date.today(), "%d-%m-%Y")
        # date_planned = datetime.strftime(date_planned, '%d-%m-%y')
        string = "Closing Inventory as at " + today
        statement_id = self.env["bank.statement.reconciliation"].browse(
            data["statement_id"]
        )
        docs = []
        # vals = data['vals']

        return {
            #'doc_ids': data['ids'],
            #'doc_model': data['model'],
            #'vals':vals,
            "string": string,
            "statement_id": statement_id,
            "docs": docs,
        }
