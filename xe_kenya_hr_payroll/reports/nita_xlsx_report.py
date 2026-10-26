from odoo import models


class NITAXlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.nita_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "NITA Report xlsx"

    def generate_xlsx_report(self, workbook, data, objs):
        emp_data = data["emp_data"]
        header_format = workbook.add_format(
            {"font_size": 10, "align": "center", "bold": True, "font_name": "Arial"}
        )
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        format3 = workbook.add_format(
            {"font_size": 10, "align": "right", "font_name": "Arial"}
        )

        sheet = workbook.add_worksheet("nssf_report")
        row = 1
        report_header = "NITA Report of " + str(data["form"]["date_year"])
        sheet.merge_range(0, 0, 0, 3, report_header, header_format)
        sheet.write(row, 0, "NITA NO", format1)
        sheet.write(row, 1, "NAME", format1)
        sheet.write(row, 2, "KRA PIN", format1)
        sheet.write(row, 3, "NITA DEDUCTION", format1)
        row += 1
        for emp in emp_data:
            sheet.write(row, 0, emp["nita_no"] or "", format2)
            sheet.write(row, 1, emp["name"], format2)
            sheet.write(row, 2, emp["krn_no"] or "", format2)
            sheet.write(row, 3, emp["nita_amt"], format3)
            row += 1
        sheet.set_column(0, 4, 20)
