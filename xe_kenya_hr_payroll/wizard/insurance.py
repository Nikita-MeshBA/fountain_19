from datetime import datetime

from odoo import models, fields, api
from ..models.constants import (
    MONTH_SELECTION,
    YEAR_SELECTION,
)


class InsuranceReportWizard(models.TransientModel):
    _name = "insurance.report.wizard"
    _description = "Ins wiz"

    date_start = fields.Selection(
        MONTH_SELECTION,
        string="Month",
    )
    date_end = fields.Selection(
        YEAR_SELECTION,
        string="Year",
    )

    def get_lines(self):
        date_start = self.date_start
        date_end = self.date_end
        docs = []
        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search([], order="name asc")
        )
        for employee in employees:
            employee_payslips = self.env["hr.payslip"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("state", "=", "done"),
                ]
            )

            for employee_payslip in employee_payslips:
                create_date_datetime_object = datetime.strptime(
                    str(employee_payslip.date_from), "%Y-%m-%d"
                )
                if str(create_date_datetime_object.month) == str(date_start) and str(
                    create_date_datetime_object.year
                ) == str(date_end):
                    insurance_payslip_lines = self.env["hr.payslip.line"].search(
                        [
                            ("employee_id", "=", employee.id),
                            ("code", "=", "INSP"),
                            ("slip_id", "=", employee_payslip.id),
                        ]
                    )
                    insurance_sum = 0
                    for insurance_payslip_line in insurance_payslip_lines:
                        insurance_sum = insurance_payslip_line.total
                        docs.append(
                            {
                                "payroll_no": employee.identification_id,
                                "employee": employee.name,
                                "id_no": employee.identification_id,
                                "amount": insurance_sum,
                            }
                        )
            final_vals = {"docs": docs}
        return final_vals

    def get_report(self):
        """Call when button 'Get Report' clicked."""
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "date_start": self.date_start,
                "date_end": self.date_end,
                "final_vals": self.get_lines(),
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref("xe_kenya_hr_payroll.insurance_report").report_action(
            self, data=data
        )


class ReportInsurance(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = "report.xe_kenya_hr_payroll.insurance_report_view"
    _description = "Insurance Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data["form"]["date_start"]
        date_end = data["form"]["date_end"]

        years_list = MONTH_SELECTION
        date_start_string = ""
        for years in years_list:
            if date_start == years[0]:
                date_start_string = years[1]

        return {
            "doc_ids": data["ids"],
            "doc_model": data["model"],
            "final_val": data["form"]["final_vals"],
            "date_start": date_start_string,
            "date_end": date_end,
        }
