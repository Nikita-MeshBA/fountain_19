from datetime import datetime

from odoo import models


class NHIFXlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.nhif_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Nhif Report xlsx"

    def generate_xlsx_report(self, workbook, data, payslip):
        date_start = payslip.date_start
        date_end = payslip.date_end
        yyyy_mm = data["form"]["yyyy_mm"]

        company = self.env["res.company"].search([], order="name asc")

        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("nhif_report")
        sheet.set_column(0, 1, 25)

        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search(
                [("emp_type", "=", "kenyan"), ("contract_type", "=", "regular")],
                order="name asc",
            )
        )
        row = 0
        for employee in employees:
            nhif_amount = self.env["hr.payslip.line"].search(
                [("employee_id", "=", employee.id), ("code", "=", "NHIF")]
            )
            date = self.env["hr.payslip"].search(
                [("employee_id", "=", employee.id), ("state", "=", "done")]
            )

            for nhif_date in date:
                create_date_datetime_object = datetime.strptime(
                    str(nhif_date.date_from), "%Y-%m-%d"
                )
                if str(create_date_datetime_object.month) == str(date_start) and str(
                    create_date_datetime_object.year
                ) == str(date_end):
                    nhif_sum = 0
                    for nhif_total in nhif_amount:
                        nhif_sum = nhif_total.total


                    employee_name = employee.name.split(" ", 1)
                    try:
                        first_name = employee_name[0]
                    except IndexError:
                        first_name = ""
                    try:
                        last_name = employee_name[1]
                    except IndexError:
                        last_name = ""
                    sheet.write(row, 0, employee.employee_no, format2)
                    sheet.write(row, 1, last_name, format2)
                    sheet.write(row, 2, first_name, format2)
                    sheet.write(row, 3, employee.identification_id, format2)
                    sheet.write(row, 4, employee.nhif_no, format2)
                    sheet.write(row, 5, nhif_sum, format2)
                    row += 1
                    sheet.write(row, 4, "Total", format1)
                    sheet.write_formula(row, 5, "{=SUM(F6:E%s)}" % (str(row)), format1)
