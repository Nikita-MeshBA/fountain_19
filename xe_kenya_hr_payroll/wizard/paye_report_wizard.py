from odoo import models, fields
from ..models.constants import (
    MONTH_SELECTION,
    YEAR_SELECTION,
)


class PAYEReportWizard(models.TransientModel):
    _name = "paye.report.wizard"
    _description = "Paye Report Wizard"

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
        return self.env.ref("xe_kenya_hr_payroll.paye_xlsx_report").report_action(
            self, data=data
        )
