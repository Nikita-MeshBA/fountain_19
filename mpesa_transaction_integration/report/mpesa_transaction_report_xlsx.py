# pylint: disable=E0401,C0114,C0115,C0116
from odoo import models

total_column = {}
sub_total_column = {}


class MpesaTransactionXlsx(models.AbstractModel):
    _name = "report.mpesa_transaction_integration.mpesa_transaction_xlsx"
    _description = "Mpesa Transaction Xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizard):
        result = data["transaction_data"]
        title = "MPesa Transactions & Paybill"
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format0 = workbook.add_format(
            {"font_size": 12, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("Transaction_Details")
        sheet.write(0, 3, title, format0)
        sheet.write(2, 0, "Start Date :", format1)
        sheet.write(2, 1, data["start_date"], format1)
        sheet.write(3, 0, "End Date :", format1)
        sheet.write(3, 1, data["end_date"], format1)
        sheet.write(5, 0, "Name", format1)
        sheet.write(5, 1, "Type", format1)
        sheet.write(5, 2, "Date", format1)
        sheet.write(5, 3, "Bill Reference", format1)
        sheet.write(5, 4, "Invoice", format1)
        sheet.write(5, 5, "Amount", format1)
        sheet.set_column(0, 5, 20)
        i = 5
        for rec in result:
            i = i + 1
            sheet.write(i, 0, rec["name"], format2)
            sheet.write(i, 1, rec["transaction_type"], format2)
            sheet.write(i, 2, rec["date"], format2)
            sheet.write(i, 3, rec["bill_ref_number"], format2)
            sheet.write(i, 4, rec["invoice_name"], format2)
            sheet.write(i, 5, rec["trans_amount"], format2)
