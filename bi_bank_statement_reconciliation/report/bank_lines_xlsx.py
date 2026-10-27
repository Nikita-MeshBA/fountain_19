from odoo import models


class ExportTemplatePurchaseLineImport(models.AbstractModel):
    _name = "report.bi_bank_statement_reconciliation.export_bank_lines_xlsx"
    _description = "Export Bank Lines XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        statement_id = self.env["bank.statement.reconciliation"].browse(
            data["statement_id"]
        )
        worksheet = workbook.add_worksheet(statement_id.name)
        # format_wrap_text = workbook.add_format({"text_wrap": "true"})
        worksheet.write("A2", "Name")
        worksheet.write("B2", statement_id.name)
        worksheet.write("A3", "Start Date")
        start_date_obj = statement_id.start_date.strftime("%d/%m/%Y")
        worksheet.write("B3", start_date_obj)
        worksheet.write("A4", "End Date")
        end_date_obj = statement_id.end_date.strftime("%d/%m/%Y")
        worksheet.write("B4", end_date_obj)

        worksheet.write("E2", "Opening Balance")
        worksheet.write("F2", "{:.2f}".format(statement_id.opening_balance))
        worksheet.write("E3", "Book Closing Balance")
        worksheet.write("F3", "{:.2f}".format(statement_id.book_closing_balance))
        worksheet.write("E4", "Bank Closing Balance")
        worksheet.write("F4", "{:.2f}".format(statement_id.actual_closing_balance))
        worksheet.write("E4", "Difference")
        worksheet.write("F4", "{:.2f}".format(statement_id.difference))

        worksheet.write("A6", "Date")
        worksheet.write("B6", "Number")
        worksheet.write("C6", "Label")
        worksheet.write("D6", "Partner")
        worksheet.write("E6", "Debit")
        worksheet.write("F6", "Credit")
        worksheet.write("G6", "Currency")
        worksheet.write("H6", "Reference")

        row = 7
        # for line in statement_id.line_ids.filtered(lambda x: not x.is_present_bank_statement):
        for line in statement_id.line_ids:
            date_obj = line.date.strftime("%d/%m/%Y")
            worksheet.write("A%s" % row, date_obj)
            worksheet.write("B%s" % row, line.move_name)
            worksheet.write("C%s" % row, line.name)
            worksheet.write("D%s" % row, line.partner_id.name)
            worksheet.write("E%s" % row, "{:.2f}".format(line.debit))
            worksheet.write("F%s" % row, "{:.2f}".format(line.credit))
            worksheet.write("G%s" % row, line.currency_id.name)
            worksheet.write("H%s" % row, line.reference)
            row += 1
