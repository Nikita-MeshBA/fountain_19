from odoo import api, fields, models, _


class HrPayslipInherit(models.Model):
    _inherit = "hr.payslip"

    def calculate_longtermadvance(self):
        payslip_obj = self
        payslip_line_obj = self.env["hr.payslip.line"]
        employee_id = payslip_obj.employee_id and payslip_obj.employee_id.id
        date_from = payslip_obj.date_from
        date_to = payslip_obj.date_to
        advance_lines = self.env["zimbabwe.hr.long.term.advance.line"].search(
            [
                ("employee_id", "=", employee_id),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("payslip_id", "=", False),
            ]
        )

        long_term_amount_tot = 0
        for line in advance_lines:
            if line.mode == "add":
                salary_rule_id = self.env.ref(
                    "l10n_zimbabwe_payroll.hr_rule_longtermadvance"
                ).id
            else:
                salary_rule_id = self.env.ref(
                    "l10n_zimbabwe_payroll.hr_rule_longtermadvance_ded"
                ).id
                long_term_amount_tot = long_term_amount_tot + line.amount

            salary_rule_obj = self.env["hr.salary.rule"].browse(salary_rule_id)
            payslip_line_obj.create(
                {
                    "name": salary_rule_obj.name,
                    "code": salary_rule_obj.code,
                    "category_id": salary_rule_obj.category_id
                    and salary_rule_obj.category_id.id,
                    "contract_id": self.contract_id.id,
                    "slip_id": self.id,
                    "quantity": 1,
                    "sequence": salary_rule_obj.sequence,
                    "salary_rule_id": salary_rule_id,
                    "amount": line.amount,
                    "long_term_advance_subline_id": line.id,
                }
            )
        long_term_amount_tot = -1 * long_term_amount_tot
        return long_term_amount_tot

    def compute_sheet(self):
        for payslip in self:
            payslip.contract_id.age_compute()
            number = payslip.number or self.env["ir.sequence"].next_by_code(
                "salary.slip"
            )
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or self.get_contract(
                payslip.employee_id, payslip.date_from, payslip.date_to
            )
            lines = [
                (0, 0, line)
                for line in self._get_payslip_lines(contract_ids, payslip.id)
            ]

            long_term_amount = payslip.calculate_longtermadvance()
            payslip.write({"line_ids": lines, "number": number})

            payslip_lines_zero_value = self.env["hr.payslip.line"].search(
                [("slip_id", "=", payslip.id), ("total", "=", 0)]
            )

            if payslip_lines_zero_value:
                payslip_lines_zero_value.unlink()

            payslip.adjust_long_term_amount(long_term_amount)
        return True

    def adjust_long_term_amount(self, long_term_amount):
        payslip_obj = self
        payslip_line_obj = self.env["hr.payslip.line"]
        net_salary_rule_id = (
            self.env["hr.salary.rule"].search([("code", "=", "NET")]).id
        )
        net_line = payslip_line_obj.search(
            [
                ("slip_id", "=", payslip_obj.id),
                ("salary_rule_id", "=", net_salary_rule_id),
            ]
        )
        net_amount = net_line.amount + long_term_amount
        net_line.write({"amount": net_amount})
