from datetime import datetime

from odoo import models, fields, api
from ..models.constants import (
    MONTH_SELECTION,
    YEAR_SELECTION,
)


class NSSFReportWizard(models.TransientModel):
    _name = "nssf.report.wizard"
    _description = "NSSF"

    def get_lines(self):
        date_start = self.date_start
        date_end = self.date_end

        docs = []
        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search([("emp_type", "=", "kenyan")], order="name asc")
        )

        for employee in employees:
            date = self.env["hr.payslip"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("state", "=", "done"),
                ]
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

                    emp_name = employee.name
                    pin_no = employee.pin_no
                    split_name = emp_name.split(" ")
                    len_name = len(split_name)
                    surname = split_name[len_name - 1]
                    other_name = emp_name.replace(surname, "")
                    if other_name:
                        other_name = other_name.strip()
                    docs.append(
                        {
                            "payroll_no": employee.employee_no,
                            "surname": surname,
                            "other_name": other_name,
                            "id_no": employee.identification_id,
                            "pin_no": pin_no,
                            "nssf_no": employee.nssf_no,
                            "total": gross_sum,
                        }
                    )
            final_vals = {"docs": docs}
        return final_vals

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
                "final_vals": self.get_lines(),
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref("xe_kenya_hr_payroll.nssf_report").report_action(
            self, data=data
        )

    def get_xlsx_report(self):
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
        return self.env.ref("xe_kenya_hr_payroll.nssf_xlsx_report").report_action(
            self, data=data
        )


class ReportNSSF(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = "report.xe_kenya_hr_payroll.nssf_report_view"
    _description = "NSSF Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data["form"]["date_start"]
        date_end = data["form"]["date_end"]
        res_config = self.env["res.config.settings"].search([], limit=1)
        nssf_no = res_config.nssf_no

        years_list = MONTH_SELECTION
        date_start_string = ""
        for tuple in years_list:
            if date_start == tuple[0]:
                date_start_string = tuple[1]

        return {
            "doc_ids": data["ids"],
            "doc_model": data["model"],
            "date_start": date_start_string,
            "date_end": date_end,
            "nssf_no": nssf_no,
            "final_val": data["form"]["final_vals"],
        }
