from datetime import datetime

from odoo import models


class PAYEXlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.paye_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Paye Report xlsx"

    def generate_xlsx_report(self, workbook, data, payslip):
        month = payslip.date_start
        year = payslip.date_end
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("paye_report")
        sheet.set_column(0, 40, 10)
        # sheet.write(0, 0, "PIN of employee", format1)
        # sheet.write(0, 1, "NAME", format1)
        # sheet.write(0, 2, "Residential Status", format1)
        # sheet.write(0, 3, "Type of employee", format1)
        # sheet.write(0, 4, "Basic Salary", format1)
        # sheet.write(0, 5, "Housing allowance", format1)
        # sheet.write(0, 6, "Transport allowance", format1)
        # sheet.write(0, 7, "leave pay", format1)
        # sheet.write(0, 8, "Overtime allowance", format1)
        # sheet.write(0, 9, "Directo´s fee", format1)
        # sheet.write(0, 10, "Lump sum payment if any", format1)
        # sheet.write(0, 11, "Other Allowance", format1)
        # sheet.write(0, 12, "Total Cash pay (A)", format1)
        # sheet.write(
        #     0,
        #     13,
        #     "Value for car benefit (value of car benefit from D_Computation_of_Car_Benefit)(B)",
        #     format1,
        # )
        # sheet.write(0, 14, "Other Non Cash Benefits", format1)
        # sheet.write(
        #     0, 15, "Total Non Cash Pay (D)=(B+C) (C if greater than 3,000)", format1
        # )
        # sheet.write(
        #     0, 16, "Global Income (Incase of non full time service Director)", format1
        # )
        # sheet.write(0, 17, "Type of Housing", format1)
        # sheet.write(0, 18, "Rent of House/Market Value", format1)
        # sheet.write(0, 19, "Computed Rent of House (F)", format1)
        # sheet.write(0, 20, "Rent Recovered from Employee (G)", format1)
        # sheet.write(0, 21, "Net Value of Housing (Ksh) (H)=(F-G)", format1)
        # sheet.write(0, 22, "Total Gross Pay (Ksh) (I)=(A+D+E+H))", format1)
        # sheet.write(0, 23, "30% of Cash Pay (J)=(A)*30%", format1)
        # sheet.write(0, 24, "Actual contribution (K)", format1)
        # sheet.write(0, 25, "Permissible Limit (L)", format1)
        # sheet.write(
        #     0,
        #     26,
        #     "Mortgage Interest (Max 150,000 Kshs or 12,500 Kshs a month) (M)",
        #     format1,
        # )
        # sheet.write(
        #     0,
        #     27,
        #     "Deposit on Home Owneship Saving Plan (Max 48,000 Kshs or 4,000 Kshs a month) (N)",
        #     format1,
        # )
        # sheet.write(
        #     0,
        #     28,
        #     "Amount of Benefit (O) = (Lower of J,K,L+M or N whichever is higher)",
        #     format1,
        # )
        # sheet.write(0, 29, "Taxable Pay (Ksh) (P) = (I-O)", format1)
        # sheet.write(0, 30, "Tax Payable (kshs) (Q) = (P)*Slab Rate", format1)
        # sheet.write(0, 31, "Monthly Personal Relief (kshs)", format1)

        # sheet.write(
        #     0,
        #     32,
        #     "Amount of Insurance Relief (Total of ¨Amount of Insurance Releif¨ fro E_Computation_Of_Insu_Relief) (Ksh) (S)",
        #     format1,
        # )
        # sheet.write(0, 33, "PAYE Tax (Ksh) (T) = (Q -R -S)", format1)
        # sheet.write(0, 34, "Self Assessed PAYE NET Tax (Ksh)", format1)

        payslips = self.env["hr.payslip"].search([])
        row = 0
        for rec in payslips:
            datetime_object = datetime.strptime(str(rec.date_from), "%Y-%m-%d")
            if str(datetime_object.month) == str(month) and str(
                datetime_object.year
            ) == str(year):
                pin_no = rec.employee_id and rec.employee_id.pin_no or ""

                emp_name = rec.employee_id and rec.employee_id.name or ""

                residential_status = (
                    rec.employee_id
                    and rec.employee_id.residential_status_id
                    and rec.employee_id.residential_status_id.name
                    or ""
                )

                type_of_employee = (
                    rec.employee_id
                    and rec.employee_id.type_of_employee_id
                    and rec.employee_id.type_of_employee_id.name
                    or ""
                )
                basic = 0
                house_allowance = 0
                transport_allowance = 0
                leave_pay = 0
                ot_allowance = 0
                director_fee = 0
                lump_sum = 0
                other_allowance = 0
                type_of_housing = "Benefit not Given"
                nssf = 0
                monthly_personal_relief = 0
                monthly_insurance_relief = 0
                paye = 0
                housing_levy_amount = 0
                insurance_relief = 0
                payslip_lines = rec.line_ids
                for line in payslip_lines:
                    if line.salary_rule_id.code == "BASIC":
                        basic = line.total

                    if line.salary_rule_id.code == "HRA":
                        house_allowance = line.total

                    if line.salary_rule_id.code == "TRA":
                        transport_allowance = line.total
                    if line.salary_rule_id.code == "LP":
                        leave_pay = line.total

                    if line.salary_rule_id.code == "OT":
                        ot_allowance = line.total
                    if line.salary_rule_id.code == "DF":
                        director_fee = line.total

                    if line.salary_rule_id.code == "LMP":
                        lump_sum = line.total
                    if line.salary_rule_id.code == "EXT":
                        other_allowance = line.total

                    if line.salary_rule_id.code == "MPR":
                        monthly_personal_relief = line.total
                    if line.salary_rule_id.code == "MIR":
                        monthly_insurance_relief = line.total
                    if line.salary_rule_id.code == "NSSF":
                        nssf = line.total
                    if line.salary_rule_id.code == "PAYE":
                        paye = line.total
                    if line.salary_rule_id.code == "HSLVR":
                        housing_levy_amount = line.total
                    if line.salary_rule_id.code == "INS_RELIEF":
                        insurance_relief = line.total

                sheet.write(row, 0, pin_no, format2)
                sheet.write(row, 1, emp_name, format2)
                sheet.write(row, 2, residential_status, format2)
                sheet.write(row, 3, type_of_employee, format2)
                sheet.write(row, 4, basic, format2)
                sheet.write(row, 5, house_allowance, format2)
                sheet.write(row, 6, transport_allowance, format2)
                sheet.write(row, 7, leave_pay, format2)
                sheet.write(row, 8, ot_allowance, format2)
                sheet.write(row, 9, director_fee, format2)
                sheet.write(row, 10, lump_sum, format2)
                sheet.write(row, 11, other_allowance, format2)

                sheet.write(row, 12, "", format2)
                sheet.write(row, 13, 0, format2)
                sheet.write(row, 14, 0, format2)
                sheet.write(row, 15, "", format2)
                sheet.write(row, 16, 0, format2)
                sheet.write(row, 17, type_of_housing, format2)
                sheet.write(row, 18, "", format2)
                sheet.write(row, 19, "", format2)
                sheet.write(row, 20, "", format2)
                sheet.write(row, 21, "", format2)
                sheet.write(row, 22, "", format2)
                sheet.write(row, 23, "", format2)
                sheet.write(row, 24, nssf, format2)
                sheet.write(row, 25, "", format2)
                sheet.write(row, 26, insurance_relief, format2)
                sheet.write(row, 27, housing_levy_amount, format2)
                sheet.write(row, 28, "", format2)
                sheet.write(row, 29, "", format2)
                sheet.write(row, 30, "", format2)
                sheet.write(row, 31, "", format2)

                sheet.write(row, 32, monthly_personal_relief, format2)
                sheet.write(row, 33, monthly_insurance_relief, format2)
                sheet.write(row, 34, "", format2)
                sheet.write(row, 35, paye, format2)
                row += 1
