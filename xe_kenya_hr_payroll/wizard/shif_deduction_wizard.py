# -*- coding: utf-8 -*-
import io
import base64
import xlsxwriter
from datetime import datetime
from odoo import api, fields, models


class ShifDeductionReportWizard(models.TransientModel):
    _name = "shif.deduction.report.wizard"
    _description = "SHIF Deduction Report Wizard"

    def get_years():
        year_list = []
        for i in range(2016, 2036):
            year_list.append((str(i), str(i)))
        return year_list

    month = fields.Selection(
        [
            ("January", "January"),
            ("February", "February"),
            ("March", "March"),
            ("April", "April"),
            ("May", "May"),
            ("June", "June"),
            ("July", "July"),
            ("August", "August"),
            ("September", "September"),
            ("October", "October"),
            ("November", "November"),
            ("December", "December"),
        ]
    )
    year = fields.Selection(get_years())

    def get_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Housing Levy Report")

        format1 = workbook.add_format(
            {
                "font_size": 11,
                "align": "left",
                "bold": True,
                "font_name": "Arial",
            }
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "left", "font_name": "Arial"}
        )
        format3 = workbook.add_format(
            {
                "font_size": 11,
                "align": "left",
                "bold": True,
                "font_name": "Arial",
            }
        )

        row = 0
        col = 0
        sheet.set_column(0, 10, 20)

        company_id = self.env.company
        payslip_month = self.month + "-" + self.year

        payslip_ids = self.env["hr.payslip"].search(
            [
                ("payslip_month", "=", payslip_month),
                ("state", "=", "done"),
                ("company_id", "=", company_id.id)
            ]
        )

        sheet.write(row, col, "Payroll Number", format3)
        sheet.write(row, col + 1, "First Name", format3)
        sheet.write(row, col + 2, "Last Name", format3)
        sheet.write(row, col + 3, "ID No", format3)
        sheet.write(row, col + 4, "KRA PIN", format3)
        sheet.write(row, col + 5, "NHIF No", format3)
        sheet.write(row, col + 6, "Contribution Amount", format3)
        sheet.write(row, col + 7, "Phone", format3)

        row += 1
        for payslip in payslip_ids:

            employee_name = payslip.employee_id.name
            split_name = employee_name.split(" ")
            first_name = split_name[0]
            last_name = employee_name.replace(first_name, "")
            if last_name:
                last_name = last_name.strip()

            amount = payslip.line_ids.filtered(lambda l: l.code == "SHIF")

            sheet.write(row, col, payslip.employee_id.employee_no or '', format2)
            sheet.write(row, col + 1, first_name or '', format2)
            sheet.write(row, col + 2, last_name or '', format2)
            sheet.write(row, col + 3, payslip.employee_id.identification_id or '', format2)
            sheet.write(row, col + 4, payslip.employee_id.pin_no or '', format2)
            sheet.write(row, col + 5, payslip.employee_id.nhif_no or '', format2)
            sheet.write(row, col + 6, amount and amount.total or '', format2)
            sheet.write(row, col + 7, payslip.employee_id.work_phone or '', format2)
            row += 1

        workbook.close()
        output.seek(0)
        generated_file = base64.encodebytes(output.read())
        output.close()
        attachment_data = {
            "name": "SHIF Deduction Report.xls",
            "datas": generated_file,
        }
        att_id = self.env["ir.attachment"].create(attachment_data)
        return {
            "type": "ir.actions.act_url",
            "url": "web/content/%s?download=true" % att_id.id,
            "target": "self",
        }
