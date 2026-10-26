from datetime import datetime

from odoo import models, fields, api
from ..models.constants import (
    MONTH_SELECTION,
    YEAR_SELECTION,
)


class HELBReportWizard(models.TransientModel):
    _name = "helb.report.wizard"
    _description = "Helb Wiz"

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
        return self.env.ref("xe_kenya_hr_payroll.helb_report").report_action(
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
        return self.env.ref("xe_kenya_hr_payroll.helb_xlsx_report").report_action(
            self, data=data
        )


class ReportHELB(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = "report.l10_kenya_hr_payroll.helb_report_view"
    _description = "Helb Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data["form"]["date_start"]
        date_end = data["form"]["date_end"]

        docs = []
        employees = self.env["hr.employee"].search([], order="name asc")
        for employee in employees:
            helb_amount = self.env["hr.payslip.line"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("code", "=", "HELB"),
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
                    for helb_total in helb_amount:
                        helb_sum = helb_total.total
                    if helb_sum > 0:
                        docs.append(
                            {
                                "payroll_no": employee.identification_id,
                                "employee": employee.name,
                                "id_no": employee.identification_id,
                                "amount": helb_sum,
                            }
                        )
        years_list = YEAR_SELECTION
        date_start_string = ""
        for tuple in years_list:
            if date_start == tuple[0]:
                date_start_string = tuple[1]

        return {
            "doc_ids": data["ids"],
            "doc_model": data["model"],
            "date_start": date_start_string,
            "date_end": date_end,
            "docs": docs,
        }
