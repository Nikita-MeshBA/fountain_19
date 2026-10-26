from datetime import datetime

from odoo import models


class NSSFXlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.nssf_report_xlsx"
    _description = "NSSF Report Xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, payslip):
        date_start = payslip.date_start
        date_end = payslip.date_end
        format1 = workbook.add_format(
            {
                "font_size": 10,
                "align": "vcenter",
                "bold": True,
                "font_name": "Arial",
                "num_format": "@",
            }
        )
        format2 = workbook.add_format(
            {
                "font_size": 10,
                "align": "vcenter",
                "font_name": "Arial",
                "num_format": "@",
            }
        )
        format3 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("nssf_report")
        sheet.write(0, 0, "PAYROLL NUMBER", format1)
        sheet.write(0, 1, "SURNAME", format1)
        sheet.write(0, 2, "OTHER NAME", format1)
        sheet.write(0, 3, "ID NO", format1)
        sheet.write(0, 4, "KRA PIN", format1)
        sheet.write(0, 5, "NSSF NO", format1)
        sheet.write(0, 6, "GROSS PAY", format1)
        sheet.write(0, 7, "VOLUNTARY", format1)

        sheet.set_column(
            0,
            1,
            25,
        )

        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search([("emp_type", "=", "kenyan")], order="name asc")
        )
        row = 1
        for employee in employees:
            emp_name = employee.name
            pin_no = employee.pin_no
            split_name = emp_name.split(" ")
            len_name = len(split_name)
            surname = split_name[len_name - 1]
            other_name = emp_name.replace(surname, "")
            if other_name:
                other_name = other_name.strip()

            date = self.env["hr.payslip"].search(
                [("employee_id", "=", employee.id), ("state", "=", "done")]
            )

            for nssf_date in date:
                create_date_datetime_object = datetime.strptime(
                    str(nssf_date.date_from), "%Y-%m-%d"
                )
                if str(create_date_datetime_object.month) == str(date_start) and str(
                    create_date_datetime_object.year
                ) == str(date_end):

                    gross_amount = self.env["hr.payslip.line"].search(
                         [
                            ("employee_id", "=", employee.id),
                            ("code", "=", "GROSS"),
                            ("slip_id","=", nssf_date.id)
                        ]
                    )
                    gross_sum = 0
                    for gross_total in gross_amount:
                        gross_sum += gross_total.total

                    sheet.write(row, 0, employee.employee_no, format2)
                    sheet.write(row, 1, surname, format2)
                    sheet.write(row, 2, other_name, format2)
                    sheet.write(row, 3, employee.identification_id, format2)
                    sheet.write(row, 4, pin_no, format2)
                    sheet.write(row, 5, employee.nssf_no, format2)
                    sheet.write(row, 6, gross_sum, format3)
                    row += 1
