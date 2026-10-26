from datetime import datetime

from odoo import models, fields, api
from ..models.constants import (
    MONTH_SELECTION,
    YEAR_SELECTION,
)


class NHIFReportWizard(models.TransientModel):
    _name = "nhif.report.wizard"
    _description = "NHIF"

    def get_lines(self):
        date_start = self.date_start
        date_end = self.date_end

        docs = []
        employees = (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search(
                [("emp_type", "=", "kenyan"), ("contract_type", "=", "regular")],
                order="name asc",
            )
        )
        for employee in employees:
            nhif_amount = self.env["hr.payslip.line"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("name", "=", "NHIF"),
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
                    nhif_sum = 0
                    for nhif_total in nhif_amount:
                        nhif_sum = nhif_total.total
                    employee_name = employee.name.split(" ", 1)
                    try:
                        first_name = employee_name[0]
                    except IndexError:
                        first_name = ""
                    try:
                        last_name = employee_name[1]
                    except IndexError:
                        last_name = ""
                    docs.append(
                        {
                            "payroll_no": employee.employee_no,
                            "sir_name": first_name,
                            "last_names": last_name,
                            "id_no": employee.identification_id,
                            "nhif_no": employee.nhif_no,
                            "amount": nhif_sum,
                        }
                    )

            final_vals = {"docs": docs}

        return final_vals

    date_start = fields.Selection(
        MONTH_SELECTION,
        string="Month",
        required=True,
    )
    date_end = fields.Selection(
        YEAR_SELECTION,
        string="Year",
        required=True,
    )

    def get_report(self):
        """Call when button 'Get Report' clicked."""
        mm = self.date_start

        if len(mm) < 2:
            mm = "0" + mm
        yyyy = self.date_end
        yyyy_mm = yyyy + "-" + mm

        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "date_start": self.date_start,
                "date_end": self.date_end,
                "yyyy_mm": yyyy_mm,
                "final_vals": self.get_lines(),
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref("xe_kenya_hr_payroll.nhif_report").report_action(
            self, data=data
        )

    def get_xlsx_report(self):
        mm = self.date_start
        if len(mm) < 2:
            mm = "0" + mm
        yyyy = self.date_end
        yyyy_mm = yyyy + "-" + mm
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "date_start": self.date_start,
                "date_end": self.date_end,
                "yyyy_mm": yyyy_mm,
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref("xe_kenya_hr_payroll.nhif_xlsx_report").report_action(
            self, data=data
        )


class ReportNHIF(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = "report.xe_kenya_hr_payroll.nhif_report_view"
    _description = "NHIF Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data["form"]["date_start"]
        date_end = data["form"]["date_end"]
        yyyy_mm = data["form"]["yyyy_mm"]

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
            "final_val": data["form"]["final_vals"],
            "yyyy_mm": yyyy_mm,
        }
