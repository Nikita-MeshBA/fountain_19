# -*- coding: utf-8 -*-

# pylint: disable=E0401

import io
from datetime import datetime

# from odoo.modules import get_module_resource
from pathlib import Path
from odoo import models


class P9Xlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.p9_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "p9 Report xlsx"

    def generate_xlsx_report1(self, workbook, data, payslip):
        employee_id = payslip.employee_id
        year = payslip.year

        company = self.env["res.company"].search([], order="name asc")

        format1 = workbook.add_format(
            {
                "font_size": 10,
                "align": "center",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
                "text_wrap": True,
            }
        )

        format11 = workbook.add_format(
            {
                "font_size": 10,
                "align": "right",
                "font_name": "Arial",
                "border": 1,
                "text_wrap": True,
            }
        )
        footer_format = workbook.add_format(
            {
                "font_size": 10,
                "align": "left",
                "bold": True,
                "font_name": "Arial",
                "text_wrap": True,
            }
        )
        format2_footer = workbook.add_format(
            {"font_size": 10, "align": "left", "font_name": "Arial", "text_wrap": True}
        )
        total_format = workbook.add_format(
            {
                "font_size": 10,
                "align": "right",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
            }
        )
        heading = workbook.add_format(
            {
                "font_size": 18,
                "align": "center",
                "bold": True,
                "font_name": "Trechubet MS",
            }
        )
        subheading = workbook.add_format(
            {
                "font_size": 12,
                "align": "center",
                "bold": True,
                "font_name": "Trechubet MS",
            }
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "right", "font_name": "Arial"}
        )
        format_2 = workbook.add_format(
            {"font_size": 10, "align": "center", "font_name": "Arial", "bold": True}
        )
        sheet = workbook.add_worksheet("paye_report")

        sheet.merge_range("E1:I1", "KENYA REVENUE AUTHORITY", heading)
        sheet.merge_range("E2:I2", "INCOME TAX DEPARTMENT", subheading)
        sheet.merge_range("E4:I4", "TAX DEDUCTION CARD - " + str(year), heading)
        sheet.merge_range("B5:C5", "Employer Name:", format_2)
        sheet.merge_range("D5:G5", company.name, format_2)
        sheet.merge_range("B6:C6", "Employee's Name:", format_2)
        sheet.merge_range("D6:G6", employee_id.name, format_2)

        sheet.merge_range("I5:J5", "Employer's PIN:", format_2)
        sheet.merge_range("K5:L5", company.vat, format_2)
        sheet.merge_range("I6:J6", "Employee's PIN:", format_2)
        sheet.merge_range("K6:L6", employee_id.pin_no, format_2)
        sheet.set_row(0, 27)
        sheet.set_row(1, 20)
        sheet.set_row(2, 20)
        sheet.set_row(3, 35)
        sheet.set_column(0, 20, 18)

        sheet.write(9, 1, "MONTH", format1)
        sheet.write(9, 2, "Basic Pay", format1)
        sheet.write(9, 3, "Benefits Non Cash", format1)
        sheet.write(9, 4, "Value of Quarters", format1)
        sheet.write(9, 5, "Total GROSS Pay", format1)
        sheet.merge_range("G10:I10", "Defined Contributions Retirement Scheme", format1)
        sheet.write(9, 9, "Home Ownership Savings Plan", format1)
        sheet.write(9, 10, "Retirement Contribution & Saving plans", format1)
        sheet.write(9, 11, "Chargeable Pay", format1)
        sheet.write(9, 12, "Tax Charged PAYE", format1)
        sheet.write(9, 14, "Personal Relief", format1)
        sheet.write(9, 13, "Insurance Relief", format1)
        sheet.write(9, 15, "PAYE Net Tax", format1)
        sheet.set_row(9, 30)
        sheet.write(10, 1, "", format1)
        sheet.write(11, 1, "", format1)
        sheet.write(10, 2, "Kshs.", format1)
        sheet.write(10, 3, "Kshs.", format1)
        sheet.write(10, 4, "Kshs.", format1)
        sheet.write(10, 5, "Kshs.", format1)
        sheet.merge_range("G11:I11", "Kshs", format1)
        sheet.write(10, 9, "Kshs.", format1)
        sheet.write(10, 10, "Kshs.", format1)
        sheet.write(10, 11, "Kshs.", format1)
        sheet.write(10, 12, "Kshs.", format1)
        sheet.write(10, 13, "Kshs.", format1)
        sheet.write(10, 14, "Kshs.", format1)
        sheet.write(10, 15, "Kshs.", format1)
        sheet.write(11, 2, "A", format1)
        sheet.write(11, 3, "B", format1)
        sheet.write(11, 4, "C", format1)
        sheet.write(11, 5, "D", format1)
        sheet.merge_range("G12:I12", "E", format1)
        sheet.write(11, 9, "F", format1)
        sheet.write(11, 10, "G", format1)
        sheet.write(11, 11, "H", format1)
        sheet.write(11, 12, "J", format1)
        sheet.write(11, 13, "K", format1)
        sheet.write(11, 15, "L", format1)
        sheet.write(12, 1, "", format1)
        sheet.write(12, 2, "", format1)
        sheet.write(12, 3, "", format1)
        sheet.write(12, 4, "", format1)
        sheet.write(12, 5, "", format1)
        sheet.write(12, 9, "", format1)
        sheet.write(12, 10, "", format1)
        sheet.write(12, 11, "", format1)
        sheet.write(12, 12, "", format1)
        sheet.write(12, 15, "", format1)
        sheet.write(
            12, 6, "Defined contribution and Retirement Scheme 30% of A", format1
        )
        sheet.write(
            12, 7, "Defined contribution and Retirement Scheme Actual Cont.", format1
        )
        sheet.write(
            12, 8, "Defined contribution and Retirement Scheme Legal Limit", format1
        )
        sheet.merge_range("N13:O13", "Total", format1)
        sheet.set_row(12, 35)
        date = self.env["hr.payslip"].search(
            [("employee_id", "=", employee_id.id), ("state", "=", "done")],
            order="date_from asc",
        )

        row = 13
        for date_year in date:
            create_date_datetime_object = datetime.strptime(
                str(date_year.date_from), "%Y-%m-%d"
            )
            if str(create_date_datetime_object.year) == str(year):
                payslip_lines = self.env["hr.payslip.line"].search(
                    [("slip_id", "=", date_year.id)]
                )
                mpr_sum = 0
                nssf_sum = 0
                ts_sum = 0
                tc_sum = 0
                nhif_sum = 0
                medical_insurance = 0
                personal_relief = 0
                paye_tax = 0

                for payslip_line in payslip_lines:
                    sheet.write(
                        row, 1, create_date_datetime_object.strftime("%B"), format11
                    )
                    if payslip_line.code == "GROSS":
                        basic_sum = payslip_line.total
                        sheet.write(row, 2, basic_sum, format11)

                    sheet.write(row, 3, 0, format11)
                    sheet.write(row, 4, 0, format11)
                    if payslip_line.code == "NHIF":
                        nhif_sum = payslip_line.total

                    if payslip_line.code == "MIR":
                        medical_insurance = payslip_line.total

                    if payslip_line.code == "MPR":
                        personal_relief = payslip_line.total

                    nfif_insurance = (
                        ((15 / 100) * nhif_sum)
                        + ((15 / 100) * medical_insurance)
                        + personal_relief
                    )

                    if payslip_line.code == "GROSS":
                        gross_sum = payslip_line.total
                        sheet.write(row, 5, gross_sum, format11)
                    if payslip_line.code == "GROSS":
                        thirty_perc = (payslip_line.total * 30) / 100
                        sheet.write(row, 6, thirty_perc, format11)

                    if payslip_line.code == "NSSF":
                        nssf_sum = payslip_line.total

                    sheet.write(row, 7, nssf_sum, format11)
                    sheet.write(row, 10, nssf_sum, format11)
                    sheet.write(row, 9, 0, format11)

                    if payslip_line:
                        sheet.write(row, 8, 20000, format11)
                    if payslip_line.code == "TS":
                        ts_sum = payslip_line.total
                    sheet.write(row, 11, ts_sum, format11)
                    if payslip_line.code == "TC":
                        tc_sum = payslip_line.total
                    sheet.write(row, 12, tc_sum, format11)

                    if payslip_line.code == "MPR":
                        mpr_sum += payslip_line.total
                        sheet.merge_range(row, 13, row, 14, nfif_insurance, format11)
                        paye_tax = tc_sum - payslip_line.total
                    sheet.write(row, 15, paye_tax, format11)
                    if payslip_line.code == "MIR":
                        mpr_sum += payslip_line.total
                        paye_tax = tc_sum - payslip_line.total
                        sheet.merge_range(row, 13, row, 14, mpr_sum, format11)
                    sheet.write(row, 15, paye_tax, format11)
                row += 1
        sheet.write(row, 1, "TOTALS", format1)

        sheet.write_formula(row, 2, "{=SUM(C13:C%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 3, "{=SUM(D13:D%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 4, "{=SUM(E13:E%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 5, "{=SUM(F13:F%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 6, "{=SUM(G13:G%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 7, "{=SUM(H13:H%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 8, "{=SUM(I13:I%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 9, "{=SUM(J13:J%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 10, "{=SUM(K13:K%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 11, "{=SUM(L13:L%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 12, "{=SUM(M13:M%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 14, "{=SUM(N13:N%s)}" % (str(row)), total_format)
        sheet.write_formula(row, 15, "{=SUM(P13:P%s)}" % (str(row)), total_format)
        sum_row = row
        row += 2

        sheet.merge_range(row, 1, row, 3, "TOTAL CHARGEABLE PAY (COL.H)", format1)
        sheet.write_formula(row, 4, "{=L%s}" % (str(sum_row + 1)), total_format)

        sheet.merge_range(row, 9, row, 10, "TOTAL TAX (COL. L)", format1)
        sheet.write_formula(row, 11, "{=P%s}" % (sum_row + 1), total_format)
        row += 2

        sheet.merge_range(
            row,
            9,
            row,
            13,
            "(b)Attach (l) Photostar copy of preceding years certificate or confirmation on ",
            format2_footer,
        )
        row += 2

        sheet.merge_range(
            row,
            10,
            row,
            13,
            "current years borrowing if applicable from the fincancial institution ",
            format2_footer,
        )

        row += 2

        sheet.merge_range(
            row,
            10,
            row,
            13,
            "(ii) the DECLARATION duly signed by the employee to form P9A",
            format2_footer,
        )
        row += 2
        sheet.write(row, 1, "IMPORTANT", footer_format)

        sheet.merge_range(
            row,
            9,
            row,
            13,
            "NAMES OF FINANCIAL INSTITIUTION ADVANCING MORTAGE LOAN ",
            footer_format,
        )
        row += 1
        sheet.write(row, 1, "1 ", format2)
        sheet.write(row, 2, "Use P9A ", format2)
        sheet.merge_range(
            row,
            3,
            row,
            7,
            "(a) For all liable employees and where director/employee "
            "receives benefits in addition to cash emoiuments",
            format2_footer,
        )
        sheet.merge_range(
            row, 9, row, 13, "____________________________________", footer_format
        )
        row += 2
        sheet.merge_range(
            row,
            3,
            row,
            7,
            "(b) Where an employee is eligible to deduction on owner "
            "occupier interest and total interest payable in Kshs 100,000/= and above",
            format2_footer,
        )
        sheet.merge_range(
            row, 9, row, 11, "L.R.NO. OF OWNDER OCCUPIED PROPERTY", footer_format
        )
        row += 2
        sheet.write(row, 1, "2 ", format2)
        sheet.merge_range(
            row,
            2,
            row,
            7,
            "(a) Deductible interest in respect of any month must be standard "
            "Kshs 8,333/=expected for December where the amount shall be 8,337/=",
            format2_footer,
        )

        sheet.merge_range(row, 9, row, 11, "DATE OF OCCUPATION HOUSE", footer_format)
        row += 2

    def generate_xlsx_report(self, workbook, data, payslip):
        employee_id = payslip.employee_id
        year = payslip.year
        company = self.env["res.company"].search([], order="name asc")

        format1 = workbook.add_format(
            {
                "font_size": 10,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
                "text_wrap": True,
            }
        )
        format2 = workbook.add_format(
            {
                "font_size": 10,
                "align": "center",
                "valign": "vcenter",
                "font_name": "Arial",
                "border": 1,
                "text_wrap": True,
            }
        )
        format3 = workbook.add_format(
            {
                "font_size": 10,
                "align": "left",
                "bold": True,
                "font_name": "Arial",
                "text_wrap": True,
            }
        )
        format_3 = workbook.add_format(
            {"font_size": 10, "align": "left", "font_name": "Arial", "text_wrap": True}
        )
        total_format = workbook.add_format(
            {
                "font_size": 10,
                "align": "center",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
            }
        )
        heading = workbook.add_format(
            {
                "font_size": 18,
                "align": "center",
                "bold": True,
                "valign": "top",
                "font_name": "Trechubet MS",
            }
        )
        subheading = workbook.add_format(
            {
                "font_size": 12,
                "align": "center",
                "bold": True,
                "valign": "top",
                "font_name": "Trechubet MS",
            }
        )
        format_2 = workbook.add_format(
            {"font_size": 10, "align": "left", "font_name": "Arial", "bold": True}
        )
        sheet = workbook.add_worksheet("paye_report")

        # logo_path = get_module_resource(
        #     "xe_kenya_hr_payroll", "static/src/img", "kenya_revenue_authority_logo.png"
        # )
        # logo = io.BytesIO(open(logo_path, "rb").read())
        logo_path = (
                Path(__file__).resolve().parents[1]
                / "static"
                / "src"
                / "img"
                / "kenya_revenue_authority_logo.png"
        )

        with open(logo_path, "rb") as logo_file:
            logo = io.BytesIO(logo_file.read())
        image_width = 120.0
        image_height = 300.0

        cell_width = 250
        cell_height = 280

        x_scale = cell_width / image_width
        y_scale = cell_height / image_height

        sheet.merge_range("F1:J4", "")
        sheet.insert_image(
            "F1:J4",
            "logo.png",
            {"image_data": logo, "x_scale": x_scale, "y_scale": y_scale},
        )

        row = 4
        col = 0

        sheet.set_column(0, 14, 15)
        sheet.set_row(row, 30)
        sheet.set_row(row + 1, 30)
        sheet.set_row(row + 2, 30)
        sheet.merge_range(
            row, col + 5, row, col + 9, "KENYA REVENUE AUTHORITY", heading
        )
        sheet.merge_range(
            row + 1, col + 5, row + 1, col + 9, "INCOME TAX DEPARTMENT", subheading
        )
        sheet.merge_range(
            row + 2,
            col + 5,
            row + 2,
            col + 9,
            "TAX DEDUCTION CARD - " + str(year),
            heading,
        )

        row += 4
        sheet.merge_range(row, col, row, col + 1, "Employer Name:", format_2)
        sheet.merge_range(row, col + 2, row, col + 3, self.env.company.name, format_2)
        sheet.merge_range(row + 1, col, row + 1, col + 1, "Employee's Name:", format_2)
        sheet.merge_range(
            row + 1, col + 2, row + 1, col + 3, employee_id.name, format_2
        )
        sheet.merge_range(row, col + 5, row, col + 6, "Employer's PIN:", format_2)
        sheet.merge_range(row, col + 7, row, col + 8, self.env.company.vat, format_2)
        sheet.merge_range(
            row + 1, col + 5, row + 1, col + 6, "Employee's PIN:", format_2
        )
        sheet.merge_range(
            row + 1, col + 7, row + 1, col + 8, employee_id.pin_no, format_2
        )

        row += 3
        sheet.set_row(row, 50)
        sheet.write(row, col, "MONTH", format1)
        sheet.write(row, col + 1, "Basic Pay", format1)
        sheet.write(row, col + 2, "Benefits Non Cash", format1)
        sheet.write(row, col + 3, "Value of Quarters", format1)
        sheet.write(row, col + 4, "Total GROSS Pay", format1)
        sheet.merge_range(
            row,
            col + 5,
            row,
            col + 7,
            "Defined Contributions Retirement Scheme",
            format1,
        )
        sheet.write(row, col + 8, "Home Ownership Savings Plan", format1)
        sheet.write(row, col + 9, "Retirement Contribution & Saving plans", format1)
        sheet.write(row, col + 10, "Chargeable Pay", format1)
        sheet.write(row, col + 11, "Tax Charged PAYE", format1)
        sheet.write(row, col + 12, "Personal Relief", format1)
        sheet.write(row, col + 13, "Insurance Relief", format1)
        sheet.write(row, col + 14, "PAYE Net Tax", format1)

        row += 1
        sheet.write(row, col, "", format1)
        sheet.write(row, col + 1, "KSHS.", format1)
        sheet.write(row, col + 2, "KSHS.", format1)
        sheet.write(row, col + 3, "KSHS.", format1)
        sheet.write(row, col + 4, "KSHS.", format1)
        sheet.merge_range(row, col + 5, row, col + 7, "KSHS.", format1)
        sheet.write(row, col + 8, "KSHS.", format1)
        sheet.write(row, col + 9, "KSHS.", format1)
        sheet.write(row, col + 10, "KSHS.", format1)
        sheet.write(row, col + 11, "KSHS.", format1)
        sheet.write(row, col + 12, "KSHS.", format1)
        sheet.write(row, col + 13, "KSHS.", format1)
        sheet.write(row, col + 14, "KSHS.", format1)

        row += 1
        sheet.write(row, col, "", format1)
        sheet.write(row, col + 1, "A", format1)
        sheet.write(row, col + 2, "B", format1)
        sheet.write(row, col + 3, "C", format1)
        sheet.write(row, col + 4, "D", format1)
        sheet.merge_range(row, col + 5, row, col + 7, "E", format1)
        sheet.write(row, col + 8, "F", format1)
        sheet.write(row, col + 9, "G", format1)
        sheet.write(row, col + 10, "H", format1)
        sheet.write(row, col + 11, "J", format1)
        sheet.write(row, col + 12, "K", format1)
        sheet.write(row, col + 13, "", format1)
        sheet.write(row, col + 14, "L", format1)

        row += 1
        sheet.set_row(row, 45)
        sheet.write(row, col, "", format1)
        sheet.write(row, col + 1, "", format1)
        sheet.write(row, col + 2, "", format1)
        sheet.write(row, col + 3, "", format1)
        sheet.write(row, col + 4, "", format1)
        sheet.write(
            row,
            col + 5,
            "E1 \n Defined contribution and Retirement Scheme 30% of A",
            format1,
        )
        sheet.write(
            row,
            col + 6,
            "E2 \n Defined contribution and Retirement Scheme Actual Cont.",
            format1,
        )
        sheet.write(
            row,
            col + 7,
            "E3 \n Defined contribution and Retirement Scheme Legal Limit",
            format1,
        )
        sheet.write(row, col + 8, "", format1)
        sheet.write(row, col + 9, "", format1)
        sheet.write(row, col + 10, "", format1)
        sheet.write(row, col + 11, "", format1)
        sheet.write(row, col + 12, "", format1)
        sheet.write(row, col + 13, "", format1)
        sheet.write(row, col + 14, "", format1)

        first_row = row + 1
        row += 1
        payslip_id = self.env["hr.payslip"].search(
            [
                ("employee_id", "=", employee_id.id),
                ("state", "=", "done"),
                ("credit_note", "=", False),
            ],
            order="date_from asc",
        )
        for payslip in payslip_id:
            create_date_datetime_object = datetime.strptime(
                str(payslip.date_from), "%Y-%m-%d"
            )
            if str(create_date_datetime_object.year) == str(year):
                payslip_lines = self.env["hr.payslip.line"].search(
                    [("slip_id", "=", payslip.id)]
                )

                gross_amt = 0
                nssf_amt = 0
                personal_relief_amt = 0
                insurance_relief_amt = 0
                for payslip_line in payslip_lines:
                    if payslip_line.code == "GROSS":
                        gross_amt += payslip_line.total

                    if payslip_line.code == "NSSF":
                        nssf_amt += payslip_line.total

                    if payslip_line.code == "MPR":
                        personal_relief_amt += payslip_line.total

                    if payslip_line.code == "NIR":
                        insurance_relief_amt += payslip_line.total

                pension_contribution_amt = 0
                percent_15_insurance_amt = 0
                if payslip.contract_id:
                    pension_contribution_amt += payslip.contract_id.pension_contribution
                    if payslip.contract_id.insurance_premium:
                        percent_15_insurance_amt += (
                            payslip.contract_id.insurance_premium * 15
                        ) / 100

                e1_col = 0
                e2_col = 0
                e3_col = 20000
                if gross_amt:
                    e1_col += (gross_amt * 30) / 100
                if nssf_amt or pension_contribution_amt:
                    e2_col += nssf_amt + pension_contribution_amt

                retirement_interest_amt = e2_col
                chargeable_amt = gross_amt - e2_col

                tc_amt = 0
                if chargeable_amt and chargeable_amt <= 24000:
                    tc_amt += (chargeable_amt * 10) / 100
                if chargeable_amt and 24001 <= chargeable_amt <= 32333:
                    amt_25 = ((chargeable_amt - 24000) * 25) / 100
                    tc_amt += amt_25 + 2400
                if chargeable_amt and chargeable_amt > 32333:
                    amt_30 = ((chargeable_amt - 24000 - 8333) * 30) / 100
                    tc_amt += amt_30 + 2400 + float(2083.25)

                new_insurance_relief_amt = (
                    percent_15_insurance_amt + insurance_relief_amt
                )
                paye_tax_amt = tc_amt - personal_relief_amt - new_insurance_relief_amt

                sheet.write(
                    row, col, create_date_datetime_object.strftime("%B"), format2
                )
                sheet.write(row, col + 1, gross_amt, format2)
                sheet.write(row, col + 2, "-", format2)
                sheet.write(row, col + 3, "-", format2)
                sheet.write(row, col + 4, gross_amt, format2)
                sheet.write(row, col + 5, e1_col, format2)
                sheet.write(row, col + 6, e2_col, format2)
                sheet.write(row, col + 7, e3_col, format2)
                sheet.write(row, col + 8, "-", format2)
                sheet.write(row, col + 9, retirement_interest_amt, format2)
                sheet.write(row, col + 10, chargeable_amt, format2)
                sheet.write(row, col + 11, tc_amt, format2)
                sheet.write(row, col + 12, personal_relief_amt, format2)
                sheet.write(row, col + 13, new_insurance_relief_amt, format2)
                sheet.write(
                    row, col + 14, paye_tax_amt if paye_tax_amt > 0 else 0, format2
                )
                row += 1

        last_row = row
        sheet.write(row, col, "Total", format1)
        sheet.write_formula(
            row,
            col + 1,
            "{=SUM(B%s:B%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write(row, col + 2, "-", total_format)
        sheet.write(row, col + 3, "-", total_format)
        sheet.write_formula(
            row,
            col + 4,
            "{=SUM(E%s:E%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 5,
            "{=SUM(F%s:F%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 6,
            "{=SUM(G%s:G%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 7,
            "{=SUM(H%s:H%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write(row, col + 8, "-", total_format)
        sheet.write_formula(
            row,
            col + 9,
            "{=SUM(J%s:J%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 10,
            "{=SUM(K%s:K%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 11,
            "{=SUM(L%s:L%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 12,
            "{=SUM(M%s:M%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 13,
            "{=SUM(N%s:N%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.write_formula(
            row,
            col + 14,
            "{=SUM(O%s:O%s)}" % (str(first_row), str(last_row)),
            total_format,
        )

        row += 2
        sheet.merge_range(
            row,
            col + 1,
            row,
            col + 2,
            "TOTAL CHARGEABLE PAY (COL. H) KSHS",
            total_format,
        )
        sheet.write_formula(
            row,
            col + 3,
            "{=SUM(K%s:K%s)}" % (str(first_row), str(last_row)),
            total_format,
        )
        sheet.merge_range(
            row, col + 9, row, col + 10, "TOTAL TAX (COL L) KSHS", total_format
        )
        sheet.write_formula(
            row,
            col + 11,
            "{=SUM(O%s:O%s)}" % (str(first_row), str(last_row)),
            total_format,
        )

        row += 3
        sheet.write(row, col + 1, "IMPORTANT", format3)
        sheet.write(row + 1, col + 1, "1. Use P9A", format3)
        sheet.merge_range(
            row + 1,
            col + 2,
            row + 2,
            col + 5,
            "(a) For all liable employees and where director/employee received "
            "\n benefits in addition to cash emoluments",
            format_3,
        )
        sheet.merge_range(
            row + 3,
            col + 2,
            row + 3,
            col + 5,
            "(b) Where an employee is eligible to deduction on owner occupier interest.",
            format_3,
        )
        sheet.write(row + 4, col + 1, "2.", format3)
        sheet.merge_range(
            row + 4,
            col + 2,
            row + 5,
            col + 5,
            "(a) Deductible interest in respect of any month must not exceed Kshs. "
            "8,333/= except for \n December where the amount shall be Kshs.8,337/=",
            format_3,
        )

        sheet.merge_range(
            row + 1,
            col + 9,
            row + 2,
            col + 12,
            "(b) Attach (i) Photostat copy of interest certificate "
            "and statement of account from the Financial Institution",
            format_3,
        )
        sheet.merge_range(
            row + 3,
            col + 9,
            row + 3,
            col + 12,
            "(ii) The DECLARATION duly signed by the employee to form P9A.",
            format_3,
        )

        sheet.merge_range(
            row + 5,
            col + 9,
            row + 5,
            col + 12,
            "NAMES OF FINANCIAL INSTITUTION ADVANCING MORTGAGE LOAN",
            format3,
        )
        sheet.merge_range(
            row + 7,
            col + 9,
            row + 7,
            col + 12,
            "L.R. NO. OF OWNER OCCUPIED PROPERTY",
            format3,
        )
        sheet.merge_range(
            row + 9, col + 9, row + 9, col + 12, "DATE OF OCCUPATION OF HOUSE", format3
        )
