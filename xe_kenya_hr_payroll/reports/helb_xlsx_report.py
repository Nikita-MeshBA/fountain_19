from datetime import datetime

from odoo import models


class HELBXlsx(models.AbstractModel):
    _name = "report.l10_kenya_hr_payroll.helb_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Helb xlsx"

    def generate_xlsx_report(self, workbook, data, payslip):
        date_start = payslip.date_start
        date_end = payslip.date_end

        company = self.env["res.company"].search([], order="name asc")

        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("helb_report")

        sheet.write(0, 0, "Employer Code", format1)
        sheet.write(0, 1, company.helb_no, format1)
        sheet.write(1, 0, "Employer Name", format1)
        sheet.write(1, 1, company.name, format1)
        sheet.write(2, 0, "Month of Contribution", format1)
        sheet.write(2, 1, str(date_start) + "-" + str(date_end), format1)

        sheet.write(4, 0, "Names", format1)
        sheet.write(4, 1, "ID No", format1)
        sheet.write(4, 2, "Staff No", format1)
        sheet.write(4, 3, "Amount", format1)

        sheet.set_column(0, 1, 25)

        employees = self.env["hr.employee"].search([], order="name asc")
        for employee in employees:
            helb_amount = self.env["hr.payslip.line"].search(
                [("employee_id", "=", employee.id), ("code", "=", "HELB")]
            )
            date = self.env["hr.payslip"].search(
                [("employee_id", "=", employee.id), ("state", "=", "done")]
            )
            row = 5
            for helb_date in date:
                create_date_datetime_object = datetime.strptime(
                    str(helb_date.date_from), "%Y-%m-%d"
                )
                if str(create_date_datetime_object.month) == str(date_start) and str(
                    create_date_datetime_object.year
                ) == str(date_end):
                    for helb_total in helb_amount:
                        helb_sum = helb_total.total
                    sheet.write(row, 0, employee.name, format2)
                    sheet.write(row, 1, employee.identification_id, format2)
                    sheet.write(row, 2, employee.identification_id, format2)
                    sheet.write(row, 3, helb_sum, format2)
                    row += 1
                    sheet.write(row, 2, "Total", format1)
                    sheet.write_formula(row, 3, "{=SUM(D6:D%x)}" % (row), format1)
