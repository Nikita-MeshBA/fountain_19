# -*- coding: utf-8 -*-

# pylint: disable=E0401
from datetime import datetime

from odoo import models


class BKNETSALXlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.bknetsal_xlsx_report"
    _inherit = "report.report_xlsx.abstract"
    _description = "Bank Net Salary Report xlsx"

    def generate_xlsx_report(self, workbook, data, payslip):
        company = self.env["res.company"].search([], order="name asc")
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("paye_report")
        sheet.set_column(0, 40, 6)
        sheet.write(0, 0, "Payment Reference", format1)
        sheet.write(0, 1, "Beneficiary Name", format1)

        sheet.write(0, 2, "", format1)
        sheet.write(0, 3, "", format1)
        sheet.write(0, 4, "", format1)
        sheet.write(0, 5, "", format1)
        sheet.write(0, 6, "Account Number", format1)
        sheet.write(0, 7, "Bank Code", format1)
        sheet.write(0, 8, "Branch Code", format1)
        sheet.write(0, 9, "Amount", format1)
        sheet.write(0, 10, "Swift Code", format1)
        sheet.write(0, 11, "Currency", format1)

        payslip_lines = self.env["hr.payslip.line"].search([("code", "=", "NET")])
        row = 1
        for line in payslip_lines:
            datetime_object = datetime.strptime(str(line.slip_id.date_from), "%Y-%m-%d")
            if str(datetime_object.month) == str(payslip.date_start) and str(
                datetime_object.year
            ) == str(payslip.date_end):
                payment_reference = data["form"]["yymm"]

                emp_name = (
                    line.slip_id
                    and line.slip_id.employee_id
                    and line.slip_id.employee_id.name
                    or ""
                )

                account_number = (
                    line.slip_id
                    and line.slip_id.employee_id
                    and line.slip_id.employee_id.debit_account_id
                    or ""
                )

                bank_code = (
                    line.slip_id
                    and line.slip_id.employee_id
                    and line.slip_id.employee_id.bic_id
                    and line.slip_id.employee_id.bic_id.bic
                    or ""
                )

                branch_code = (
                    line.slip_id
                    and line.slip_id.employee_id
                    and line.slip_id.employee_id.branch_code
                    or ""
                )
                amount = 0

                if line.salary_rule_id.code == "NET":
                    amount = line.total

                swift_code = (
                    line.slip_id
                    and line.slip_id.employee_id
                    and line.slip_id.employee_id.swift_code
                    or ""
                )

                currency = (
                    company and company.currency_id and company.currency_id.name or ""
                )

                sheet.write(row, 0, payment_reference, format2)
                sheet.write(row, 1, emp_name, format2)

                sheet.write(row, 2, "", format2)
                sheet.write(row, 3, "", format2)
                sheet.write(row, 4, "", format2)
                sheet.write(row, 5, "", format2)

                sheet.write(row, 6, account_number, format2)

                sheet.write(row, 7, bank_code, format2)
                sheet.write(row, 8, branch_code, format2)
                sheet.write(row, 9, amount, format2)
                sheet.write(row, 10, swift_code, format2)
                sheet.write(row, 11, currency, format2)

                row += 1
