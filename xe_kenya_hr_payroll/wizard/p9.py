from odoo import models, fields
from ..models.constants import (
    YEAR_SELECTION,
)


class P9Wizard(models.TransientModel):
    _name = "p9.report.wizard"
    _description = "P9 wizard"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        domain="['|',('active','=',True),('active','=',False)]",
    )
    year = fields.Selection(YEAR_SELECTION)

    def get_xlsx_report(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "form": {
                "employee_id": self.employee_id,
                "year": self.year,
            },
        }
        return self.env.ref("xe_kenya_hr_payroll.p9_xlsx_report").report_action(
            self, data=data
        )
