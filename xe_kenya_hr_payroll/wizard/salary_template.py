from datetime import datetime

from odoo import models, fields, api
from ..models.constants import (
    MONTH_SELECTION,
    YEAR_SELECTION,
)


class SalaryReportWizard(models.TransientModel):
    _name = "salary.report.wizard"
    _description = "sal wiz"

    date_start = fields.Selection(
        MONTH_SELECTION,
        string="Month",
    )
    date_end = fields.Selection(
        YEAR_SELECTION,
        string="Year",
    )

    def get_report(self):
        """Call when button 'Get Report' clicked."""
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "date_start": self.date_start,
                "date_end": self.date_end,
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref("xe_kenya_hr_payroll.salary_report").report_action(
            self, data=data
        )


class ReportSalary(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = "report.xe_kenya_hr_payroll.salary_report_view"
    _description = "Salary Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data["form"]["date_start"]
        date_end = data["form"]["date_end"]

        docs = []
        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search([], order="name asc")
        )
        for employee in employees:
            net_amount = self.env["hr.payslip.line"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("code", "=", "NET"),
                ]
            )
            date = self.env["hr.payslip"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("state", "=", "done"),
                ]
            )

            for nhif_date in date:
                create_date_datetime_object = datetime.strptime(
                    str(nhif_date.date_from), "%Y-%m-%d"
                )
                if str(create_date_datetime_object.month) == str(date_start) and str(
                    create_date_datetime_object.year
                ) == str(date_end):
                    net_sum = 0
                    for net_total in net_amount:
                        net_sum = net_total.total
                    docs.append(
                        {
                            "payroll_no": employee.identification_id,
                            "employee": employee.name,
                            "amount": net_sum,
                            "bic_id": employee.bic_id.name,
                            "branch_code": employee.branch_code,
                            "credit_account": employee.primary_bank_account_id.acc_number,
                            "debit_account": employee.debit_account_id,
                        }
                    )
        years_list = MONTH_SELECTION
        date_start_string = ""
        for years_tuple in years_list:
            if date_start == years_tuple[0]:
                date_start_string = years_tuple[1]

        return {
            "doc_ids": data["ids"],
            "doc_model": data["model"],
            "date_start": date_start_string,
            "date_end": date_end,
            "final_vals": docs,
        }
