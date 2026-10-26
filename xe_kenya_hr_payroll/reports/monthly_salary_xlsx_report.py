from odoo import models


class P9Xlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.ms_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Monthly Salary Report xlsx"

    def generate_xlsx_report(self, workbook, data, payslip):
        state = data["state"]
        if state == "done":
            state_search_condition = ("state", "=", "done")
        elif state == "draft":
            state_search_condition = ("state", "=", "draft")
        elif state == "verify":
            state_search_condition = ("state", "=", "verify")
        else:
            state_search_condition = ("state", "in", ("done", "draft", "verify"))
        payslip_month = data["payslip_month"]
        company = self.env["res.company"].search([], order="name asc")
        format1 = workbook.add_format(
            {
                "font_size": 10,
                "align": "center",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
            }
        )
        format_footer = workbook.add_format(
            {"font_size": 10, "align": "center", "bold": True, "font_name": "Arial"}
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
            {"font_size": 10, "align": "center", "font_name": "Arial", "border": 1}
        )
        format3 = workbook.add_format(
            {"font_size": 10, "align": "right", "font_name": "Arial", "border": 1}
        )
        format4 = workbook.add_format(
            {
                "font_size": 10,
                "align": "right",
                "bold": True,
                "font_name": "Arial",
                "border": 1,
            }
        )
        sheet = workbook.add_worksheet("ms_report")
        header_string = str(company.name) + " Payroll Summary " + payslip_month
        sheet.merge_range(1, 1, 1, 18, header_string, subheading)

        salary_structure_rules_name = (
            self.env["hr.payroll.structure"]
            .search([("id", "=", data["salary_structure_id"])])
            .rule_ids.mapped("name")
            if self.env["hr.payroll.structure"]
            .search([("id", "=", data["salary_structure_id"])])
            .rule_ids
            else False
        )
        salary_structure_rules_ids = (
            self.env["hr.payroll.structure"]
            .search([("id", "=", data["salary_structure_id"])])
            .rule_ids.mapped("id")
            if self.env["hr.payroll.structure"]
            .search([("id", "=", data["salary_structure_id"])])
            .rule_ids
            else False
        )

        row = 4
        col = 4
        sheet.write(row, 0, "Staff No", format1)
        sheet.write(row, 1, "Name", format1)
        sheet.write(row, 2, "Function/Position", format1)
        sheet.write(row, 3, "Worked Days", format1)

        if salary_structure_rules_name:
            for rule_name in salary_structure_rules_name:
                sheet.write(row, col, rule_name, format1)
                col += 1

        row += 1
        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search([], order="name asc")
        )
        for employee in employees:
            payslip_id = self.env["hr.payslip"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("payslip_month", "=", payslip_month),
                    state_search_condition,
                    ('struct_id','=',data['salary_structure_id'])
                ]
            )
            for payslip in payslip_id:
                sheet.write(row, 0, employee.employee_no, format2)
                sheet.write(row, 1, employee.name, format2)
                sheet.write(row, 2, employee.job_title, format2)
                workline = payslip.worked_days_line_ids.filtered(
                    lambda line: line.code == "WORK100"
                )
                if workline:
                    sheet.write(row, 3, workline.number_of_days, format3)
                else:
                    sheet.write(row, 3, 0, format3)

                rule_col = 4
                if payslip.line_ids:
                    for rule_id in salary_structure_rules_ids:
                        payslip_line_id = payslip.line_ids.filtered(
                            lambda l: l.salary_rule_id.id == rule_id
                        )
                        if payslip_line_id:
                            sheet.write(row, rule_col, payslip_line_id.total, format3)
                        else:
                            sheet.write(row, rule_col, 0, format3)
                        rule_col += 1
                else:
                    for rule_id in salary_structure_rules_ids:
                        sheet.write(row, rule_col, 0, format3)
                        rule_col += 1

                row += 1
        sheet.write(row, 3, "TOTALS", format1)

        col_alpha_name = []
        for c in range(5, 5 + len(salary_structure_rules_ids)):
            col_alpha_name.append(self.get_column_name(c))

        for index, col_name in enumerate(col_alpha_name, start=4):
            sheet.write_formula(
                row, index, "{=SUM(%s5:%s%s)}" % (col_name, col_name, str(row)), format4
            )

        row += 2
        sheet.merge_range(row, 1, row, 2, "HR Validation", format_footer)
        sheet.write(row, 3, "Prepared By", format_footer)
        sheet.write(row, 6, "Verified By", format_footer)
        row += 2
        sheet.merge_range(row, 1, row, 2, "FINANCIAL AUTHORISATION", format_footer)
        sheet.write(row, 3, "Authorised By", format_footer)
        sheet.set_column(0, 30, 15)

    def get_column_name(self, n):
        result = ""
        while n > 0:
            index = (n - 1) % 26
            result += chr(index + ord("A"))
            n = (n - 1) // 26
        return result[::-1]
