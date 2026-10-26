from datetime import date

from dateutil import relativedelta

from odoo import models, fields


class NITAReportWizard(models.TransientModel):
    _name = "nita.report.wizard"
    _description = "NITA"

    def get_years(self):
        year_list = []
        for i in range(2016, 2036):
            year_list.append((i, str(i)))
        return year_list

    date_year = fields.Selection(
        lambda self: self.get_years(), string="Year", default=date.today().year
    )

    def get_xlsx_report_data(self):
        nita_deduction_amt = (
            self.env["ir.config_parameter"].sudo().get_param("nita_deduction_amt")
        )
        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search([("emp_type", "=", "kenyan")])
        )
        year = int(self.date_year)
        year_end = date(year, 12, 31)
        year_start = date(year, 1, 1)
        current_date = date.today()
        current_month = int(str(current_date)[5:7])

        if date.today() < year_end:
            year_end = date.today()
        emp_list = []
        for emp in employees:
            emp_vals = {}
            emp_vals["nita_no"] = emp.nita_no
            emp_vals["name"] = emp.name
            emp_vals["krn_no"] = emp.pin_no
            # contracts are hr.version records since Odoo 19; several
            # versions can share one contract, so count each period once
            run_contract = self.env["hr.version"].search(
                [
                    ("employee_id", "=", emp.id),
                    ("contract_date_start", "!=", False),
                    ("contract_date_start", "<=", year_end),
                ]
            )
            contract_periods = {
                (version.contract_date_start, version.contract_date_end)
                for version in run_contract
            }
            total_months = 0
            end_year = False
            start_year = False
            for contract_start, contract_end in contract_periods:
                if contract_end and contract_end < year_start:
                    continue
                if contract_start > year_start:
                    start_year = contract_start
                else:
                    start_year = year_start
                if contract_end and contract_end < year_end:
                    end_year = contract_end
                else:
                    end_year = year_end

                diff = relativedelta.relativedelta(end_year, start_year)
                int_months = diff.months + 1
                if not end_year and not start_year:
                    int_months = 0
                total_months = total_months + int_months
            total_months = min(total_months, current_month)
            if total_months:
                deduct_amt = float(total_months) * float(nita_deduction_amt)
                emp_vals["nita_amt"] = deduct_amt

            else:
                emp_vals["nita_amt"] = 0

            emp_list.append(emp_vals)
        return emp_list

    def get_xlsx_report(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "emp_data": self.get_xlsx_report_data(),
            "form": {
                "date_year": self.date_year,
            },
        }
        return self.env.ref("xe_kenya_hr_payroll.nita_xlsx_report").report_action(
            self, data=data
        )
